from pycparser import c_parser, c_ast
from pycparser.c_ast import *


class AST_parsing:

    def __init__(self):
        self.labeled_loops = []
        self.for_loops = []

    def get_features(self, file):
        """
        This function returns a dictionary of parsed features from list of labeled loops
        :param file: path, path to the file with a source code
        :return: dict, dict with features, key is a loop, value is a dict of loop's characteristics
        """
        with open(file, 'r') as myfile:
            text = myfile.read()
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        self.get_outer_loops(ast.ext)
        self.get_labeled_loops(self.for_loops)
        self.labeled_loops = delete_empty_statements(self.labeled_loops)
        features = process_loops(self.labeled_loops)
        return features

    def get_outer_loops(self, list_of_functions):
        """
        This function takes a list of high-level objects of a given C file. For every function it finds the outermost
        loops in its body and saves them to a list
        :param list_of_functions: [FuncDef1,FuncDef2, OtherObj...] list of
        high-level objects in out AST. Only func_def will be considered
        :return: [(For1, Label) ,(For2, None),...] list of tuples for all outermost loops in a given C file. The first element is a loop,
        the second element is a label if it's known, otherwise - None.
        """
        for function in list_of_functions:
            body_items = get_block_items_for_function_def(function)
            self.process_body_items(body_items)

    def process_body_items(self, body_items):
        if not body_items is None:
            for item in body_items:
                if item.__class__ is For:
                    self.for_loops.append((item, None))

                elif item.__class__ is Label:
                    self.for_loops.append((item.stmt, item.name))

                elif item.__class__ is Compound:
                    block_items = item.block_items
                    for block_item in block_items:
                        self.process_body_items(block_item)

    def get_labeled_loops(self, list_of_outer_loops):
        """
        Find all labels for all given loop-nests and save them to the global variable labeled_loops
        :type list_of_outer_loops: [For1, For2,...]
        """
        for element in list_of_outer_loops:
            label = element[1]
            loop = element[0]
            if not label is None:  # If we have one-nested loop
                self.labeled_loops.append((loop, label, 1))
            else:
                self.process_loop_nest(loop, 1)

    def process_loop_nest(self, loop_nest, level):
        """
        Depth-first search for For-object. The function tries to find labels in a given loop-nest
        :param loop_nest: For object
        :param level:  int, loop-nest level
        """
        items = get_blocks_items_for(loop_nest)
        if self.process_block_elements(items, level):
            pass
        else:
            for item in items:
                self.process_block_elements(item, level)

    def process_block_elements(self, element, level):
        """
        This function checks whether we have Label or For. If we have a label - we add the corresponding loop to the list.
        If we have For we start a new iteration of depth-first search.
        :param element: AST-object
        :param level: int, loop-nest level
        :param iterations:  list, [(init, condition,last),...] the list that stores information that will be useful to evaluate
        the number of iterations for the most inner loop and all loops that are on the path to the innermost one
        :return: bool, True if we have single Label or For, otherwise false
        """
        if element.__class__ is Label:
            self.labeled_loops.append((element.stmt, element.name, level + 1))
            return True
        elif element.__class__ is For:
            self.process_loop_nest(element, level + 1)
            return True
        return False


def get_block_items_for_function_def(func_def):
    """
    This function takes an ast-object as a parameter. If it's a function definition, it returns
    statements inside its body. Otherwise, it returns None
    :param func_def: ast_object
    :return: (list) list of statements inside func_def or None if we don't deal with func_def
    """
    if func_def.__class__ is FuncDef:
        return func_def.body.block_items
    else:
        return None


def get_blocks_items_for(ast_object):
    """
    This function returns block items for a given ast-object (based on it's type). If the match is not found - return
    None
    :param ast_object:
    :return: block_items (list or single item)
    """
    if ast_object.__class__ is Compound:
        return ast_object.block_items

    elif ast_object.__class__ is For:
        try:
            return ast_object.stmt.block_items
        except:
            return ast_object.stmt
    elif ast_object.__class__ is Label:
        return ast_object.stmt
    return None


def process_loops(loop_list):
    """
    This function takes a list of loops and returns a dict with it's features
    :param loop_list: [loop1,loop2,...] list of loops to be parsed for hadndcrafted features
    :return: dict, dict of handcrafted features for each loop
    """
    features = {}
    for loop, label_name, level in loop_list:

        if loop.stmt.__class__ is Compound:
            statements = loop.stmt.block_items
        else:
            statements = [loop.stmt]

        features[loop] = {'label': label_name, 'statements': 0, 'writes': 0, 'reads': 0,
                          'arrays': set(), 'vars': set(), 'function_calls': 0,
                          'level': level, 'iterators': list(), 'var_and_iter': 0,
                          'floating_point_operations': 0, 'branches': 0}

        for stmt in statements:
            process_statement(stmt, features, loop)

    for value in features.values():
        number_of_arrays = len(value['arrays'])
        number_of_vars = len(value['vars'])
        number_of_iterators = len(value['iterators'])

        var_and_iter = set(value['iterators']).intersection(value['vars'])

        value['var_and_iter'] = len(var_and_iter)
        value['arrays'] = number_of_arrays
        value['vars'] = number_of_vars
        # value['iterators'] = number_of_iterators

    return features


def process_branches(if_stmt, features, loop):
    if if_stmt.iftrue.__class__ is Compound:
        features[loop]['branches'] += 1
        items = if_stmt.iftrue.block_items
        for item in items:
            process_statement(item, features, loop)

    if if_stmt.iffalse.__class__ is Compound:
        features[loop]['branches'] += 1
        items = if_stmt.iffalse.block_items
        for item in items:
            process_statement(item, features, loop)


def process_statement(stmt, features, loop):
    features[loop]['statements'] += 1

    if stmt.__class__ is Assignment:
        assignment_with_potential_float_op = ['/=', '*=', '+=', '-=']
        process_lvalue(stmt.lvalue, features, loop)
        process_rvalue(stmt.rvalue, features, loop)
        if stmt.op in assignment_with_potential_float_op:
            features[loop]['floating_point_operations'] += 1

    if stmt.__class__ is FuncCall:
        features[loop]['function_calls'] += 1
    if stmt.__class__ is If:
        process_branches(stmt, features, loop)

    if stmt.__class__ is Decl:
        features[loop]['writes'] += 1
        features[loop]['vars'].add(stmt.name)
        process_rvalue(stmt.init, features, loop)


def process_array_ref(current_array_ref, init_array_ref, features, loop, l_r_side, dimensionality=0):
    if current_array_ref.__class__ is ID:
        features[loop]['arrays'].add(current_array_ref.name)
        array_name = current_array_ref.name
        process_subscript(init_array_ref, features, loop, l_r_side, array_name, dimensionality)
    else:
        process_array_ref(current_array_ref.name, init_array_ref, features, loop, l_r_side,
                          dimensionality=dimensionality + 1)


def process_binary_op_for_subscripts(bin_op, features, loop, l_r_side, array_name, dimensionality):
    if bin_op.left.__class__ is ID:
        features[loop]['iterators'].append((array_name, dimensionality, l_r_side, bin_op.left.name))
    elif bin_op.left.__class__ is BinaryOp:
        process_binary_op_for_subscripts(bin_op.left, features, loop, l_r_side, array_name)
    if bin_op.right.__class__ is ID:
        features[loop]['iterators'].append((array_name, dimensionality, l_r_side, bin_op.right.name))
    elif bin_op.right.__class__ is BinaryOp:
        process_binary_op_for_subscripts(bin_op.right, features, loop, l_r_side, array_name)


def process_subscript(array_ref, features, loop, l_r_side, array_name, dimensionality):
    if hasattr(array_ref, 'name'):
        # name = array_ref.name
        # features[loop]['iterators'].append((array_name, l_r_side, name))
        process_subscript(array_ref.name, features, loop, l_r_side, array_name, dimensionality)
    else:
        pass
    if hasattr(array_ref, 'subscript'):
        subscript = array_ref.subscript
        if subscript.__class__ is BinaryOp:
            process_binary_op_for_subscripts(subscript, features, loop, l_r_side, array_name, dimensionality)
        else:
            if subscript.__class__ is ID:
                features[loop]['iterators'].append((array_name, dimensionality, l_r_side, subscript.name))

    else:
        pass


def process_lvalue(lval, features, loop):
    if lval.__class__ is ID:
        features[loop]['vars'].add(lval.name)
        features[loop]['writes'] += 1
    else:
        if lval.__class__ is ArrayRef:
            process_array_ref(lval, lval, features, loop, 'l')
            features[loop]['writes'] += 1

        else:
            if lval.__class__ is FuncCall:
                features[loop]['function_calls'] += 1


def process_rvalue(rval, features, loop):
    if rval.__class__ is BinaryOp:
        process_rvalue(rval.left, features, loop)
        process_rvalue(rval.right, features, loop)
        features[loop]['floating_point_operations'] += 1
    else:
        if rval.__class__ is ID:
            features[loop]['vars'].add(rval.name)
            features[loop]['reads'] += 1
        else:
            if rval.__class__ is ArrayRef:
                process_array_ref(rval, rval, features, loop, 'r')
                features[loop]['reads'] += 1

            else:
                if rval.__class__ is FuncCall:
                    features[loop]['function_calls'] += 1


def delete_empty_statements(list_of_loops):
    """
    This function returns a new list which doesn't contain empty statements
    :param list_of_loops: list of loops (may contain empty statements)
    :return: list of loops (without empty statements)
    """
    output_list_of_loops = [x for x in list_of_loops if not x[0].__class__ is EmptyStatement]
    return output_list_of_loops


