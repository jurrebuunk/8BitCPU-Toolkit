import re

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.token_specification = [
            ('FUNC',     r'func'),          # Function keyword
            ('CALL',     r'call'),          # Call keyword
            ('RET',      r'ret'),           # Return keyword
            ('WHILE',    r'while'),         # While keyword
            ('IF',       r'if'),            # If keyword
            ('ELSE',     r'else'),          # Else keyword
            ('NUMBER',   r'\d+'),           # Integer
            ('ID',       r'[A-Za-z]+'),     # Identifiers
            ('ASSIGN',   r'='),             # Assignment operator
            ('END',      r';'),             # Statement terminator
            ('OP',       r'[+\-^|&]'),      # Arithmetic and logical operators
            ('CMP',      r'[<>]=?|=='),     # Comparison operators
            ('LBRACE',   r'\{'),            # Left brace
            ('RBRACE',   r'\}'),            # Right brace
            ('LPAREN',   r'\('),            # Left parenthesis
            ('RPAREN',   r'\)'),            # Right parenthesis
            ('SKIP',     r'[ \t]+'),        # Skip over spaces and tabs
            ('NEWLINE',  r'\n'),            # Line endings
        ]   
        self.token_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.token_specification)

    def tokenize(self):
        for mo in re.finditer(self.token_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'NUMBER':
                value = int(value)
            elif kind == 'ID' and value == 'int':
                kind = 'TYPE'
            elif kind == 'SKIP' or kind == 'NEWLINE':
                continue
            self.tokens.append((kind, value))
        return self.tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        statements = []
        while self.pos < len(self.tokens):
            statements.append(self.statement())
        return statements

    def statement(self):
        if self.tokens[self.pos][0] == 'TYPE':
            return self.declaration()
        elif self.tokens[self.pos][0] == 'FUNC':
            return self.function_definition()
        elif self.tokens[self.pos][0] == 'CALL':
            return self.function_call()
        elif self.tokens[self.pos][0] == 'RET':
            self.pos += 1  # Skip 'ret'
            self.pos += 1  # Skip ';'
            return ('RET',)
        elif self.tokens[self.pos][0] == 'WHILE':
            return self.while_loop()
        elif self.tokens[self.pos][0] == 'IF':
            return self.if_statement()
        elif self.tokens[self.pos][0] == 'ID':
            return self.assignment()
        else:
            raise SyntaxError(f'Unknown statement: {self.tokens[self.pos]}')

    def if_statement(self):
        self.pos += 1  # Skip 'if'
        self.pos += 1  # Skip '('
        condition = self.expression()
        self.pos += 1  # Skip ')'
        self.pos += 1  # Skip '{'
        then_body = []
        while self.tokens[self.pos][0] != 'RBRACE':
            then_body.append(self.statement())
        self.pos += 1  # Skip '}'
        
        else_body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'ELSE':
            self.pos += 1  # Skip 'else'
            self.pos += 1  # Skip '{'
            while self.tokens[self.pos][0] != 'RBRACE':
                else_body.append(self.statement())
            self.pos += 1  # Skip '}'
        
        return ('IF', condition, then_body, else_body)
    def declaration(self):
        self.pos += 1  # Skip 'int'
        var_name = self.tokens[self.pos][1]
        self.pos += 1  # Skip variable name
        self.pos += 1  # Skip '='
        expr = self.expression()
        self.pos += 1  # Skip ';'
        return ('DECL', var_name, expr)

    def function_definition(self):
        self.pos += 1  # Skip 'func'
        func_name = self.tokens[self.pos][1]
        self.pos += 1  # Skip function name
        self.pos += 1  # Skip '{'
        body = []
        while self.tokens[self.pos][0] != 'RBRACE':
            body.append(self.statement())
        self.pos += 1  # Skip '}'
        return ('FUNC', func_name, body)

    def function_call(self):
        self.pos += 1  # Skip 'call'
        func_name = self.tokens[self.pos][1]
        self.pos += 1  # Skip function name
        self.pos += 1  # Skip ';'
        return ('CALL', func_name)

    def while_loop(self):
        self.pos += 1  # Skip 'while'
        self.pos += 1  # Skip '('
        condition = self.expression()
        self.pos += 1  # Skip ')'
        self.pos += 1  # Skip '{'
        body = []
        while self.tokens[self.pos][0] != 'RBRACE':
            body.append(self.statement())
        self.pos += 1  # Skip '}'
        return ('WHILE', condition, body)

    def assignment(self):
        var_name = self.tokens[self.pos][1]
        self.pos += 1  # Skip variable name
        self.pos += 1  # Skip '='
        expr = self.expression()
        self.pos += 1  # Skip ';'
        return ('ASSIGN', var_name, expr)

    def expression(self):
        left = self.term()
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] in ('OP', 'CMP'):
            op = self.tokens[self.pos][1]
            self.pos += 1
            right = self.term()
            left = ('BINOP', op, left, right)
        return left

    def term(self):
        token = self.tokens[self.pos]
        self.pos += 1
        if token[0] == 'NUMBER':
            return ('NUM', token[1])
        elif token[0] == 'ID':
            return ('VAR', token[1])
        else:
            raise SyntaxError('Unknown term')




class CodeGenerator:
    def __init__(self):
        self.instructions = []
        self.register_map = {}
        self.next_register = 0
        self.function_map = {}
        self.label_counter = 0

    def get_register(self, var):
        if var not in self.register_map:
            self.register_map[var] = f"R{self.next_register}"
            self.next_register += 1
        return self.register_map[var]

    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def generate(self, ast):
        for node in ast:
            self.statement(node)
        return self.instructions

    def statement(self, node):
        if node[0] == 'DECL':
            var_name = node[1]
            expr = node[2]
            reg = self.get_register(var_name)
            self.expression(expr, reg)
        elif node[0] == 'ASSIGN':
            var_name = node[1]
            expr = node[2]
            reg = self.get_register(var_name)
            self.expression(expr, reg)
        elif node[0] == 'FUNC':
            func_name = node[1]
            body = node[2]
            self.function_map[func_name] = func_name
            self.instructions.append(f"{func_name}:")
            for stmt in body:
                self.statement(stmt)
            self.instructions.append("RET")
        elif node[0] == 'CALL':
            func_name = node[1]
            self.instructions.append(f"CAL {self.function_map[func_name]}")
        elif node[0] == 'WHILE':
            condition = node[1]
            body = node[2]
            start_label = self.new_label()
            end_label = self.new_label()
            self.instructions.append(f"{start_label}:")
            cond_reg = self.get_register("cond")
            self.expression(condition, cond_reg)
            self.instructions.append(f"BRH Z, {end_label}")
            for stmt in body:
                self.statement(stmt)
            self.instructions.append(f"JMP {start_label}")
            self.instructions.append(f"{end_label}:")
        elif node[0] == 'IF':
            condition = node[1]
            then_body = node[2]
            else_body = node[3]
            else_label = self.new_label()
            end_label = self.new_label()
            cond_reg = self.get_register("cond")
            self.expression(condition, cond_reg)
            self.instructions.append(f"BRH Z, {else_label}")
            for stmt in then_body:
                self.statement(stmt)
            self.instructions.append(f"JMP {end_label}")
            self.instructions.append(f"{else_label}:")
            for stmt in else_body:
                self.statement(stmt)
            self.instructions.append(f"{end_label}:")

    def expression(self, node, dest_reg):
        if node[0] == 'NUM':
            self.instructions.append(f"LDI {dest_reg}, {node[1]}")
        elif node[0] == 'VAR':
            src_reg = self.get_register(node[1])
            if src_reg != dest_reg:
                self.instructions.append(f"LDI {dest_reg}, {src_reg}")
        elif node[0] == 'BINOP':
            op = node[1]
            left = node[2]
            right = node[3]
            left_reg = self.get_register(left[1]) if left[0] == 'VAR' else f"R{self.next_register}"
            right_reg = self.get_register(right[1]) if right[0] == 'VAR' else f"R{self.next_register + 1}"
            if left[0] == 'NUM':
                self.instructions.append(f"LDI {left_reg}, {left[1]}")
            if right[0] == 'NUM':
                self.instructions.append(f"LDI {right_reg}, {right[1]}")
            if op == '+':
                self.instructions.append(f"ADD {dest_reg}, {left_reg}, {right_reg}")
            elif op == '-':
                self.instructions.append(f"SUB {dest_reg}, {left_reg}, {right_reg}")
            elif op == '^':
                self.instructions.append(f"XOR {dest_reg}, {left_reg}, {right_reg}")
            elif op == '|':
                self.instructions.append(f"NOR {dest_reg}, {left_reg}, {right_reg}")
            elif op == '&':
                self.instructions.append(f"AND {dest_reg}, {left_reg}, {right_reg}")
            elif op == '<':
                temp_reg = self.get_register("temp")
                self.instructions.append(f"SUB {temp_reg}, {left_reg}, {right_reg}")
                self.instructions.append(f"BRH C, {dest_reg}")  # If carry, branch to dest_reg (left < right)
            elif op == '>':
                temp_reg = self.get_register("temp")
                self.instructions.append(f"SUB {temp_reg}, {right_reg}, {left_reg}")
                self.instructions.append(f"BRH C, {dest_reg}")  # If carry, branch to dest_reg (right < left)
            elif op == '==':
                self.instructions.append(f"SUB {dest_reg}, {left_reg}, {right_reg}")
                self.instructions.append(f"BRH Z, {dest_reg}")  # Branch if zero
                
code = """
int a = 5;
int b = 3;
int result = 0;

func add {
    result = a + b;
}

func multiply {
    int temp = a;
    while (b > 0) {
        result = result + temp;
        b = b - 1;
    }
}

call add;
call multiply;
"""

lexer = Lexer(code)
tokens = lexer.tokenize()
print(tokens)  # Debugging line

parser = Parser(tokens)
ast = parser.parse()

codegen = CodeGenerator()
assembly_code = codegen.generate(ast)

for instruction in assembly_code:
    print(instruction)

