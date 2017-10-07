#! /usr/bin/env python
# *-* coding: iso-8859-1 *-*
r"""
classes: Basic(), Fusion(), Compression()
attributes:
 lines => list of virtual basic lines
 arguments => 'c' compress, 'u' ultra compress,
 'remgo' show subscript name, 'loz' my copyleft,
 scriptName => if you choose an other script name
 root => root of the project
usage:Oct 24, 2014 3:16:03 PM
 code = Basic(lines,arguments,scriptName)
 code.root = "/root/folder/"
 code.basic() => method return applesoft basic

 code = Fusion(lines,root)
 code.fusion() => method merge all virtual basic scripts in one virtual basic script

 code = Compression(lines)
 code.compression() => method return more compressed applesoft basic code

classe: BasToBaz()
attributes
 lines => list of applesoft basic lines
usage:
 code = BasToBaz(lines)
 code.to_virtual() => return applesoft basic converted in virtual basic

version:
 Virtual Basic tool version 0.2.8
 Copyright � 2011, andres lozano aka loz
 Copyleft: This work is free, you can redistribute it and / or modify it
 under the terms of the Free Art License. You can find a copy of this license
 on the site Copyleft Attitude well as http://artlibre.org/licence/lal/en on other sites.
"""
import os
import pprint  # Just used for dumping data structures for debugging
import re
import json
from time import gmtime, strftime
import sys
from switch import Switch as switch
import logging


class FunctionDef:
    """Holds the definition of a VirtualBasic++ function."""

    def __init__(self, name, ret_type):
        self.name = name  # Name of the function
        self.retType = ret_type  # Type it returns
        self.stringParams = 0
        self.intParams = 0
        self.floatParams = 0
        self.totalParamCount = 0
        # Positional param arguments
        self.paramName = []
        self.paramType = []
        self.paramSet = {}  # String to set parameters in function call
        self.paramGet = {}  # String to get value in function body


class CodeLine:
    """ Holds line of source code """

    def __init__(self, filename, line_num, code):
        self.filename = filename  # Name of the file this line came from
        self.lineNum = line_num  # Line # of original source
        self.code = code


class TokenObj:
    """Holds a single applesoft token"""

    def __init__(self, filename, line_num, token_id, token_text):
        """
        Holds a single AppleSoft token
        :type token_text: basestring
        """
        self.filename = filename
        self.lineNum = line_num
        self.tokenID = token_id
        self.tokenText = token_text


class VarObj:
    """Holds a single applesoft variable"""

    def __init__(self, var_name, var_type, line_num, file_name, native_var):
        """
        Represents a variable in the source code.
        :param var_name: The name of the variable as found in the source code
        :param var_type: The type of the variable
        :param line_num: The line number on which the variable was defined
        :param file_name: The file name in which the variable was defined.
        :param native_var: Whether the variable is a native Applesoft var, or a Vbpp defined var.
        :return:
        """
        self.vbppName = var_name
        self.asoftName = None
        self.decLineNum = line_num  # Line of source code where it was defined
        self.varType = var_type
        self.fileName = file_name
        self.nativeVar = native_var


def convert_lines(file_name, lines):
    """ Convert string of code into line objects. We need to do this
        in order to be able to track the filename and original line
        number of the code, so we can return sane error messages.
    :param file_name: The name of the file this source code came from.
    :param lines: The list of source
    """

    new_code = []
    line_num = 1

    for line in lines:
        new_code.append(CodeLine(file_name, line_num, line))
        line_num += 1
    return new_code


class VirtualBasicCode:
    """class VirtualBasicCode version 0.1.5"""

    def __init__(self, li=[], args=[], naScript="none"):
        self.lines = li
        self.arguments = args
        self.step = 10
        self.incr = 10
        self.mode = "local"
        self.gotos = {}
        self.appels = {}
        self.reservedNumberedLines = []
        self.code = ""
        self.otherInsert = 0
        self.root = ""
        # self.msg = "\n"
        self.scriptName = naScript
        self.defines = {}
        self.havePreDefs = False
        self.predefvars = {}
        self.predefaplvarsnames = []
        self.tokens = []
        # Regular expression scanner to tokenize the VirtualBasoc++ source. Used
        # by the tokenizer routine. Uses the undocumeted Scanner class in the
        # Python regular expression library.
        self.tokenizer = re.Scanner([
            (r'\".*?\"', lambda scanner, token: ("STRING", token)),
            (r"[0-9]*\.[0-9]*", lambda scanner, token: ("FLOATLITERAL", token)),
            (r"^\s*[0-9]+", lambda scanner, token: ("LINENUM", token)),
            (r"[0-9]+", lambda scanner, token: ("INTLITERAL", token)),
            (r"_[a-zA-Z_][a-zA-Z_0-9\-]*", lambda scanner, token: ("LINELABELDEF", token)),
            (
                r"@[a-zA-Z_][a-zA-Z_0-9\-]*\(", lambda scanner, token: ("FUNCTIONCALL", token)),
            (r"@[a-zA-Z_][a-zA-Z_0-9\-]*", lambda scanner, token: ("LINELABELREF", token)),
            (r"\+\+|\-\-", lambda scanner, token: ("POSTOP", token)),
            (r"\+\=", lambda scanner, token: ("PLUSEQUALS", token)),
            (r"\-\=", lambda scanner, token: ("MINUSEQUALS", token)),
            (r"\bLONGIF\b", lambda scanner, token: ("LONGIF", token)),
            (r"\bENDIF\b", lambda scanner, token: ("ENDIF", token)),
            (r"\bELSEIF\b", lambda scanner, token: ("ELSEIF", token)),
            (r"\bON\b", lambda scanner, token: ("ON", token)),
            (r"\bIF\b", lambda scanner, token: ("IF", token)),
            (r"\bTHEN\b", lambda scanner, token: ("THEN", token)),
            (r"\bELSE\b", lambda scanner, token: ("ELSE", token)),
            (r"(\bREM\b|\\\\).*", lambda scanner, token: ("REMARK", token)),
            (r"\bINTEGER\b", lambda scanner, token: ("INTDEC", token)),
            (r"\bFLOAT\b", lambda scanner, token: ("FLOATDEC", token)),
            (r"\bSTRING\b", lambda scanner, token: ("STRINGDEC", token)),
            (r"\bENDFUNCTION\b", lambda scanner, token: ("FUNCEND", token)),
            (r"\bFUNCTION\b", lambda scanner, token: ("FUNCDEC", token)),
            (r"\bASSERT\b", lambda scanner, token: ("ASSERT", token)),
            (r"\bWHILE\b", lambda scanner, token: ("WHILE", token)),
            (r"\bDO\b", lambda scanner, token: ("DO", token)),
            (r"\bWEND\b", lambda scanner, token: ("WEND", token)),
            (r"\bREPEAT\b", lambda scanner, token: ("REPEAT", token)),
            (r"\bUNTIL\b", lambda scanner, token: ("UNTIL", token)),
            (r"\bBREAK\b", lambda scanner, token: ("BREAK", token)),
            (r"\bCONTINUE\b", lambda scanner, token: ("CONTINUE", token)),
            (r"[\+\-\/\*]", lambda scanner, token: ("OPERATOR", token)),
            (r"\<|\>", lambda scanner, token: ("OPERATOR", token)),
            (r"\=", lambda scanner, token: ("EQUATE", token)),
            (r"\bEND\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bPRINT\b|\?", lambda scanner, token: ("PRINT", token)),
            (r":", lambda scanner, token: ("STATEMENTSEP", token)),
            (r"\bFOR\b|\bNEXT\b|\bSTEP\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bDATA\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bINVERSE\b|\bFLASH\b", lambda scanner, token: ("KEYWORD", token)),
            (r"(\bCOLOR|\bHCOLOR){1}\s*\=", lambda scanner, token: ("KEYWORD", token)),
            (r"\bINPUT\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bDEL\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bDIM\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bREAD\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bGR\b|\bTEXT\b|\bHGR2\b|\bHGR\b", lambda scanner, token: ("KEYWORD", token)),
            (r"{\bPR|\bIN}\s*\#", lambda scanner, token: ("KEYWORD", token)),
            (r"\bCALL\b|\bPOKE\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bPLOT\b|\bHLIN\b|\bVLIN\b|\bHPLOT\b",
             lambda scanner, token: ("KEYWORD", token)),
            (r"\bDRAW\b|\bXDRAW\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bHTAB\b|\bHOME\b|\bSHLOAD\b", lambda scanner, token: ("KEYWORD", token)),
            (r"(\bROT|\bSCALE){1}\s*\=", lambda scanner, token: ("KEYWORD", token)),
            (r"\bTRACE\b|\bNOTRACE\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bNORMAL\b|\bFLASH\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bPOP\b|\bVTAB\b", lambda scanner, token: ("KEYWORD", token)),
            (r"(\bHIMEM|\bLOMEM){1}\s*\:", lambda scanner, token: ("KEYWORD", token)),
            (r"\bONERR\b|\bRESUME\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bRECALL\b|\bSTORE\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bLET\b|\bGOTO\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bRUN\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bRESTORE\b|\bGOSUB\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bRETURN\b", lambda scanner, token: ("RETURN", token)),
            (r"\&", lambda scanner, token: ("AMPERSAND", token)),
            (r"\bSTOP\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bSAVE\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bDEF\s+FN", lambda scanner, token: ("FUNCDEF", token)),
            (r"\bDEF\b", lambda scanner, token: ("VARDEC", token)),
            (r"\bCONT\b|\bLIST\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bCLEAR\b|\bGET\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bNEW\b|\bTAB\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bTO\b|\bTHEN\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bAT\b|\bGET\b", lambda scanner, token: ("KEYWORD", token)),
            (r"\bNOT\b|\bAND\b|\bOR\b", lambda scanner, token: ("OPERATOR", token)),
            (r"\bSPEED\=", lambda scanner, token: ("OPERATOR", token)),
            (r"\bTRY\b", lambda scanner, token: ("TRY", token)),
            (r"\bCATCH\b", lambda scanner, token: ("CATCH", token)),
            (r"\bENDTRY\b", lambda scanner, token: ("ENDTRY", token)),
            (r"\bSWITCH\b", lambda scanner, token: ("SWITCH", token)),
            (r"\bCASE\b", lambda scanner, token: ("CASE", token)),
            (r"\bDEFAULT\b", lambda scanner, token: ("DEFAULT", token)),
            (r"\bENDSWITCH\b", lambda scanner, token: ("ENDSWITCH", token)),
            (r"\;", lambda scanner, token: ("CONCAT", token)),
            (
                r"\bPEEK\b|\bFN\b|\bSPC\b|\bSGN\b|\bINT\b|\bABS\b|\bUSR\b|\bFRE\b|\bSCRN\b|\bPDL\b|\bPOS\b|\bSQR\b|\bRND\b|\bLOG\b",
                lambda scanner, token: ("STDFUNC", token)),
            (r"\MID\$|\bCHR\$",
             lambda scanner, token: ("STDFUNC", token)),
            (r"[a-zA-Z_][a-zA-Z_0-9]*\$\(",
             lambda scanner, token: ("STRINGARRAY", token)),
            (r"[a-zA-Z_][a-zA-Z_0-9]*\%\(", lambda scanner, token: ("INTARRAY", token)),
            (r"[a-zA-Z_][a-zA-Z_0-9]*\(", lambda scanner, token: ("FLOATARRAY", token)),
            (r"\(", lambda scanner, token: ("LPAREN", token)),
            (r"\)", lambda scanner, token: ("RPAREN", token)),
            (r"\$[a-fA-F0-9]+", lambda scanner, token: ("HEXCONSTANT", token)),
            (r"[a-zA-Z_][a-zA-Z_0-9]*\$", lambda scanner, token: ("STRINGVAR", token)),
            (r"[a-zA-Z_][a-zA-Z_0-9]*\%", lambda scanner, token: ("INTVAR", token)),
            (r"[a-zA-Z_][a-zA-Z_0-9]*", lambda scanner, token: ("IDENTIFIER", token)),
            (r"[,]+", lambda scanner, token: ("PUNCTUATION", token)),
            (r"\n", lambda scanner, token: ("EOL", token)),
            (r"[\ \t]+", lambda scanner, token: ("WHITESPACE", token)),
        ], flags=re.IGNORECASE)
        self.idTokens = ["INTVAR", "IDENTIFIER", "STRINGVAR"]  # Different types of variable identifiers
        self.varDecTokens = ["INTDEC", "FLOATDEC", "STRINGDEC"]  # Which tokens declare variables
        self.decVarList = {}  # List of decleared vars
        self.arrayRefs = ["STRINGARRAY", "INTARRAY", "FLOATARRAY"]
        self.statementSeps = ["STATEMENTSEP", "EOL"]  # Things that terminate a statement
        self.unDefVars = {}  # Variables found in the code that were declared
        self.reservedVars = {}
        self.assignedVars = {}
        self.pp = pprint.PrettyPrinter(indent=4)
        self.funcDefs = {}
        # Tokens allowed in a parameter list of a function call
        self.allowedInParameterExp = ["OPERATOR", "STRING", "FLOATLITERAL", "INTLITERAL", "POSTOP", "CONCAT",
                                      "STDFUNC", "LPAREN", "RPAREN", "STRINGARRAY", "INTARRAY", "FLOATARRAY",
                                      "STRINGVAR", "INTVAR", "IDENTIFIER", "WHITESPACE"]

        # List of two letter reserved words that can never be variable names
        self.twoLetterReservedWords = ["IN", "IF", "FN", "GR", "TO", "OR", "ON", "PR", "AT"]

    def delete_lines_with_hashes(self):
        """delete lines beginning with hash char"""
        result = []
        line_with_hash = re.compile("^\s*\#")
        for line in self.lines:
            if not line_with_hash.search(line.code):
                result.append(line)
        self.lines = result

    # Handle C++ style // comments
    def delete_double_slash_comments(self):
        """delete lines beginning with hash char"""
        result = []
        line_slash_comment = re.compile("^\s*//.*")
        line_ends_with_slash_comment = re.compile("^(.*?)(\/\/.*)$")
        for line in self.lines:
            # See if entire line is a // comment
            if not line_slash_comment.search(line.code):
                # Nope. See if it ends with a // comment
                matched = line_ends_with_slash_comment.search(line.code)
                if matched:
                    line.code = matched.group(1) + "\n"
                    result.append(line)
                else:
                    result.append(line)
        self.lines = result

    # TODO: This doesn't work? Need to fix issue with // comments sucking line below in.
    def delete_slashes(self):
        """replace char with slashes"""
        for line in self.lines:
            line = re.sub(r'\\.*$', "\n", line)

    def delete_lines_with_rem(self):
        """delete lines beginning with rem"""
        result = []
        line_with_hash = re.compile("^\s*rem", re.I)
        for line in self.lines:
            if not line_with_hash.search(line.code):
                result.append(line)
        self.lines = result

    def replace_last_hashes(self):
        """replace \# by :rem * unless it's pr# or with slashes
         Why do we even do this? It's messing things up.
        """
        # result = []
        hashes = re.compile("[^pr\\\]\#.*")
        for line in self.lines:
            line.code = hashes.sub("", line.code)
            # result.append(line)
            # self.lines = result

    def insert_files(self):
        """insert/include external files"""
        logger = logging.getLogger("VirtualBasic.insert_files")
        self.otherInsert = 0
        result = []
        insert_file = re.compile("#include ([a-zA-Z0-9\/\-\_]+\.baz)")
        # lineWithHash = re.compile("^\s*\#")
        for line in self.lines:
            if insert_file.search(line.code):
                m = insert_file.search(line.code)
                fichier = self.root + "/" + m.group(1)
                try:
                    f = open(fichier, "r")
                    code = f.readlines()
                    f.close()
                    result += convert_lines(m.group(1), code)
                except:
                    logger.error("Cannot find included file {0}".format(fichier))
                    # self.msg += "! Warning can't insert file  " +  + " ! \n"
            else:
                result.append(line)

        for line in result:
            if insert_file.search(line.code):
                self.otherInsert = 1
                break
        self.lines = result

    def delete_inserts(self):
        """delete inserts"""
        # result = []
        logger = logging.getLogger("VirtualBasic.delete_inserts")
        insert_file = re.compile("#include ([a-zA-Z0-9\/\-\_]+\.baz)")
        for line in self.lines:
            if insert_file.search(line.code):
                m = insert_file.search(line.code)
                fichier = self.root + "/" + m.group(1)
                logger.error("Deleting include for missing file {0}.".format(fichier))
                # self.msg += "! Warning can't insert file  " + fichier + ", insert  deleted ! \n"
            line.code = insert_file.sub("", line.code)
            # result.append(line)
            # self.lines = result

    def ignore_empty_lines_and_section(self):
        """ignore empty lines and sections"""
        result = []
        empty_line = re.compile("^\s*$")
        begin_section = re.compile("^[\s]*section", re.I)
        end_section = re.compile("^[\s]*finsection", re.I)
        close_section = re.compile("^[\s]*closesection", re.I)
        # tabOrSpace = re.compile("^[\t\s]*")
        for line in self.lines:
            if not (
                                empty_line.search(line.code)
                            or begin_section.search(line.code)
                        or end_section.search(line.code)
                    or close_section.search(line.code)
            ):
                # line = tabOrSpace.sub("",line) # take line and erase blank lines
                result.append(line)
        self.lines = result

    def ignore_rem_lines_with_sparks(self):
        """ignore lines beginning by REM * (spark)"""
        result = []
        rem_lines_with_spark = re.compile("^[\s]*rem \*", re.I)
        for line in self.lines:
            if not rem_lines_with_spark.search(line.code):
                result.append(line)
        self.lines = result

    def reserves_numbers(self):
        "reserves lines with numbers"
        result = []
        numbered_lines = re.compile("^([0-9]+)")
        for line in self.lines:
            if numbered_lines.search(line.code):  # protect line numbers
                m = numbered_lines.search(line.code)
                result.append(m.group(1))
        self.reservedNumberedLines = result

    def number_uppercase(self):
        """number and upcase"""
        result = []
        numbered_lines = re.compile("^[0-9]+")
        for line in self.lines:
            if numbered_lines.search(line.code):  # if first line number
                result.append(line)
            else:
                self.step += self.incr
                if str(self.step) in self.reservedNumberedLines:
                    self.step += self.incr
                if line != "":
                    line.code = str(self.step) + " " + line.code
                    result.append(line)
        # This would result in the entire program being uppercase, which isn't
        # useful.
        # for i in xrange( len( result ) ):
        # result[i] = result[i].upper()
        self.lines = result

    def replace_goto_gosub(self):
        """find gotos and gosub"""
        result = []
        gotosub = re.compile("^([0-9]+) _([a-zA-Z_][a-zA-Z_0-9\-]*)")
        for line in self.lines:
            if gotosub.search(line.code):  # position of subscript
                m = gotosub.search(line.code)
                goto_sub_name = (int(m.group(1)) + self.incr)  # add incr and go to first line
                self.gotos[m.group(2)] = str(goto_sub_name)  # $1 = number of line, $2 = subscript name
                tmp1 = "_" + m.group(2)
                tmp2 = "REM->" + m.group(2)
                # put comment about subscript
                if not self.arguments.ultracompact:
                    line.code = re.sub(tmp1, tmp2, line.code)
                    result.append(line)
            else:
                result.append(line)
        self.lines = result
        # print("\n\n\nLabels:")
        # self.pp.pprint(self.gotos)

    # Issue with the original code... it would find matches using regular expressions
    # to match the entire target name, but then blindly did a search/replace for all instances of 
    # the match in the line of code. This would result in issues of there were line labels
    # referenced in the line of code that matched a substring of another label reference.
    def replace_calls(self):
        """find and replace goto, gosub"""
        logger = logging.getLogger("VirtualBasic.replace_calls")
        result = []
        goto_sub_call = re.compile("@([a-zA-Z_][a-zA-Z_0-9\-_]*)")
        # gotosubCallAll = re.compile("[^\\\]@([a-zA-Z_][a-zA-Z_0-9\-_]*)?")
        for line in self.lines:
            # Repeatly search for line label references
            while goto_sub_call.search(line.code):
                # Split string around the matching line label
                before, ref, after = goto_sub_call.split(line.code, 1)
                replace = "???"
                if self.gotos.has_key(ref.upper()):
                    # matches a known line number. Set is as the replacement
                    replace = self.gotos[ref.upper()]
                else:
                    logger.warning('GOTO or GOSUB references unknown line label "{0}"'.format(ref))
                    # self.msg += "! Warning code not found for goto or gosub "
                    # self.msg += "\"" + ref + "\" ! \n"
                line.code = " ".join((before, replace, after))
                # line = line.rstrip()
                # FIXME: The following is a bad idea... could result in live code being commented out.
                if self.arguments.remgosubcomments:
                    line.code += ":REM GO->" + ref
            result.append(line)
        self.lines = result

    def lines_sorted(self):
        """sort lines with numbers"""
        result = []
        lines_code = {}
        # This used to break line numbers away from code, then sort on the line 
        # numbers, then reassemble. Instead, just breaking out line numbers, associating
        # that with the line object, then reordering the list of lines. Not sure if this
        # is even necessary...
        lines_numbers = re.compile("^([0-9]+) (.*)$")
        for line in self.lines:
            if lines_numbers.search(line.code):
                m = lines_numbers.search(line.code)
                my_key = eval(m.group(1))
                # lines_code[my_key] = m.group(2)
                lines_code[my_key] = line
        keys_sorted = lines_code.keys()
        keys_sorted.sort()
        for my_key in keys_sorted:
            # lineNumber = str(my_key)
            result.append(lines_code[my_key])
        self.lines = result

    # In the following few routines, there's no reason to duplicate the list
    # holding the lines... we just make changes to the list contents in
    # place. Only need to duplicate the list when adding.removing lines.
    def delete_parenthesis_comments(self):
        """delete parenthesis comments"""
        # result = []
        parenthesis_comment = re.compile("\{.+?\}")
        for line in self.lines:
            line.code = parenthesis_comment.sub("", line.code)
            # result.append(line)
            # self.lines = result

    def replace_prints(self):
        """replace print by ?"""
        # result = []
        prints = re.compile("PRINT")
        for line in self.lines:
            line.code = prints.sub("?", line.code)
            # result.append(line)
            # self.lines = result

    def replace_duplicated_colon(self):
        """replace :: by :"""
        # result = []
        duplicated_colon = re.compile("::")
        for line in self.lines:
            line.code = duplicated_colon.sub(":", line.code)
            # result.append(line)
            # self.lines = result

    # Here we need to actually duplicate the line since we're potentially dropping
    # some of them.
    def delete_rem_lines(self):
        """delete lines beginning by rem"""
        result = []
        rem_line = re.compile("^[0-9]+ REM")
        for line in self.lines:
            if not rem_line.search(line.code):
                result.append(line)
        self.lines = result

    # Probably should get rid of this... easier to do when the code is tokenized.
    def delete_spaces(self):
        """delete all useless spaces"""
        # result = []
        flag = 0
        for line in self.lines:
            tmp = ""
            for char in line.code:
                if char == "\"":
                    if flag == 1:
                        flag = 0
                    else:
                        flag = 1
                if flag == 0 and char != " ":
                    tmp += char
                if flag == 1:
                    tmp += char
            line.code = tmp
            # result.append(tmp)
            # self.lines = result

    def delete_all_comments(self):
        """delete all comments"""

        # self.replace_last_hashes()
        self.delete_parenthesis_comments()
        # self.ignoreBracketedComments()
        # self.ignore_empty_lines_and_section()
        if self.arguments.ultracompact or self.arguments.compact:
            self.ignore_rem_lines_with_sparks()

    def deconvert_lines(self):
        """Converts a list of line objects to list of strings."""
        new_code = []
        for line in self.lines:
            new_code.append(line.code)
        return new_code

    @staticmethod
    def trim_lines(lines):
        """ Remove leading and trailing whitespace and tabs. Need to do this
            since apparently the tokenizer freaks out and adds triple quotes to
            lines that end in double quires and contain a tab after it.
            i.e. foo$ = ""<tab> "" "
        :param lines: list of Code lines to trim
        """
        for line in lines:
            code = line.code
            code = code.strip() + '\n'
            line.code = code
        return lines

    def convert(self):
        logger = logging.getLogger('VirtualBasic.convert')
        """This is the main function that performs the conversion of VBPP code to
            Applesoft."""

        self.lines = convert_lines(self.scriptName, self.lines)

        self.delete_all_comments()

        if self.mode == "local" and self.root != "":  # if root not defined don't try to import insert
            self.insert_files()
            self.delete_all_comments()
            while self.otherInsert == 1:  # scan again lines to find a new insert
                self.delete_all_comments()
                self.insert_files()
        else:
            self.delete_inserts()
        # self.dumpLines(self.lines)

        # first rem clean
        if self.arguments.ultracompact:
            self.delete_lines_with_rem()

        self.delete_all_comments()
        self.delete_double_slash_comments()
        # Handle #defines and their replacement
        self.find_defs()
        self.handle_ifdef()
        # If there are no defines, skip replacing defs
        if len(self.defines) > 0:
            self.replace_defs()
        # self.dumpLines(self.lines)
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.defines)


        # For the next part, we need to tokenize the source
        self.tokens = self.tokenize(self.lines)

        # First, handle loops, exceptions, functions, and other features that will generate
        # new variable references.

        # print("Initial tokens:")
        # self.dump_tokens(self.tokens)
        self.handle_switch_statements()
        self.findFunctionDefs()
        # print("After findFunctionDefs:")
        # self.print_token_stream(self.tokens)
        self.replace_function_calls()
        # print("After replace_function_calls:")
        # self.print_token_stream(self.tokens)
        self.handle_loops()
        # self.print_token_stream(self.tokens)
        self.handle_try_catch()
        self.handle_operators()

        # Handle variables

        # See if user supplied a predefined-variable file. This is mainly used for chaining multiple
        # Vbpp files.
        if "VARFILE" in self.defines:
            self.havePreDefs = True
            self.predefvars = self.read_var_file()
            self.predefaplvarsnames = self.get_predef_apl_varnames(self.predefvars)
        # Locate the variable definitions.
        self.tokens, self.decVarList = self.find_variable_defs(self.tokens)
        # Search for any undeclared variables.
        self.unDefVars = self.find_undef_variables(self.tokens)
        # Make sure any undefined variables used in the code are assigned to defined vars
        self.reservedVars = self.reserve_native_varnames(self.unDefVars)
        # print("Reserved vars")
        # self.pp.pprint(self.reservedVars)

        if self.havePreDefs:
            # self.add_predefs_to_reserved_vars()
            self.reservedVars.update(self.predefaplvarsnames)
            logger.debug("Reserved vars after adding predefs:")
            logger.debug(self.pp.pformat(self.reservedVars))
        self.assign_names_to_defvars()
        self.replace_defined_vars()

        if self.havePreDefs:
            self.write_var_file(self.predefvars)

        # Conditional arguments and others.
        # self.handleSimpleElse()
        self.handleLongIfs()

        self.handle_asserts()
        self.remove_empty_lines_and_statements()
        self.replace_hex_constants()
        self.replace_question_marks_with_print()
        self.lines = self.de_tokenize(self.tokens)

        # print("After detokenizing")
        # self.dumpLines(self.lines)

        self.lines = self.trim_lines(self.lines)
        # print("\n\n\nAfter trimming lines")
        # self.dumpLines(self.lines)

        self.ignore_empty_lines_and_section()

        self.reserves_numbers()
        self.number_uppercase()

        # print("\n\n\nCode before replace gotoGosub")
        # self.dumpLines(self.lines)
        self.replace_goto_gosub()

        # print("\n\n\nCode before replace Calls")
        # self.dumpLines(self.lines)
        self.replace_calls()

        # print("\n\n\nCode after replace Calls")
        # self.dumpLines(self.lines)
        # self.lines_sorted()

        if self.arguments.ultracompact or self.arguments.compact:
            self.replace_prints()

        self.replace_duplicated_colon()

        if self.arguments.ultracompact:
            self.delete_rem_lines()

        version_date = strftime("%d/%m/%Y - %Hh%M", gmtime())
        tmp = "10 REM - " + self.scriptName.upper() + ".BAS - " + version_date + "\n"
        if self.arguments.loz:
            tmp += " - BY - ANDRES - AKA - LOZ - COPYLEFT"
        self.lines.insert(0, CodeLine("", 0, tmp))

        if self.arguments.ultracompact:
            self.delete_spaces()
        self.lines = self.deconvert_lines()
        self.delete_slashes()

    # New hacks added by gary

    def dump_lines(self, lines):
        """
        Print code output. Code can be a list of strings or a list of line objects.
        :param lines: a list of string containing code, or a list of line objects.
        """

        logger = logging.getLogger('VirtualBasic')

        code = ""
        dump_strings = type(lines[0]) is str
        if dump_strings:
            logger.debug("Dumping list of strings")
        else:
            logger.debug("Dumping list of line objects")
        for line in self.lines:
            if dump_strings:
                code += '"{0}'.format(line).replace('\n', '"\n')
            else:
                code += '"{0}'.format(line.code).replace('\n', '"\n')
        # print(code)
        logger.debug(code)

    def find_defs(self):
        """Find all of the #define lines and add them to a dictionary. Strips #defines from code"""
        def_re = re.compile(r"^\s*(?:#define|#alias)\s+(\w+)\s*(?:=?\s*(.+))?$", re.IGNORECASE)
        result = []
        # Search for defines
        for line in self.lines:
            matched = def_re.match(line.code)
            if matched:
                self.defines[matched.group(1)] = matched.group(2)
                # Eat the #define line so it is eliminated from file
            else:
                # Not a define line... keep it.
                result.append(line)
        self.lines = result

        # Handle defines from command line (if any)
        if self.arguments.define:
            equals_exp_re = re.compile("(\w+)=(\w+)")
            for definition in self.arguments.define:
                matched = equals_exp_re.match(definition)
                if matched:
                    self.defines[matched.group(1)] = matched.group(2)
                else:
                    self.defines[definition] = None

    def replace_defs(self):
        """Takes the dictionary built up of defines and replaces them.

        note:: This will try to replace discrete symbols in the source that match a
               definition. The intent is to replace variable names, words, etc. Using it to
               try to replace a substring won't work.
        """
        # Cribbed from http://stackoverflow.com/questions/2400504/easiest-way-to-replace-a-string-using-a-dictionary-of-replacements
        pattern = re.compile(r'\b(' + '|'.join(self.defines.keys()) + r')\b')

        for line in self.lines:
            line.code = pattern.sub(lambda x: self.defines[x.group()], line.code)
            # self.lines = result

    def handle_ifdef(self):
        """Scan if #ifdef ... #endif and #ifndef #endif"""
        results = []
        skip_stack = []  # Keep track of nested ifdef/ifndef.
        skipping = False

        ifdef_re = re.compile("^\s*(#ifdef|#ifndef)\s+(\w+)")
        endif_re = re.compile("^\s*#endif")
        for line in self.lines:
            # Do we have the start of an #if(n)def?
            matched = ifdef_re.match(line.code)
            if matched:
                # test for do not skip case
                if matched.group(1) == '#ifdef' and matched.group(2) \
                        in self.defines or matched.group(1) == '#ifndef' and \
                                matched.group(2) not in self.defines:
                    # All we need to do here is push the current skipping state
                    # onto stack. Either we have a state below us that
                    # requires skipping, or we don't. This state will never
                    # move from skipping to not skipping
                    skip_stack.append(skipping)
                    continue
                else:
                    # Must have a case where we need to skip
                    # Push current skipping state onto stack
                    skip_stack.append(skipping)
                    skipping = True
                    continue
            # See if we have an #endif
            matched = endif_re.match(line.code)
            if matched:
                # Get previous skipping state
                skipping = skip_stack.pop()
                continue  # Go to next line
            # If neither RE matched, then decide whether
            # we are skipping or not...
            if skipping:
                continue
            else:
                results.append(line)  # Keep line in source
        # Done looping though all lines
        self.lines = results

    #
    def tokenize(self, lines):
        """Tokenize the code line by line
        :param lines: List of code lines to tokenize.
        """
        tokens = []
        logger = logging.getLogger('VirtualBasic')
        # Used to combine all into a single string then tokenize. Can't
        # do that now since we want to save line # and file name infor for 
        # each token so we can print reasonable error messages.
        # Need to combine lines into one string.
        # source = "".join(code)
        for line in lines:
            linetok, remainder = self.tokenizer.scan(line.code)
            # self.tokens = results
            if not remainder is None and remainder != "":
                # Uh oh... something didn't tokenize
                logger.error("Syntax error in file {1} at line {0}:\n{3}\n Could not parse \"{2}\".".format(
                    line.lineNum, line.filename, remainder, line))

                # print("Fatal Error when tokenizing program. Error occurred at: " +
                #      remainder)
                exit(1)
            for newtoken in linetok:
                # Append new topken objects based on token tuples from RE tokenizer
                # Add info from this line of code
                new_tok = TokenObj(line.filename, line.lineNum, newtoken[0], newtoken[1])
                tokens.append(new_tok)

                # pp = pprint.PrettyPrinter(indent=4)
                # pp.pprint(self.tokens)
        return tokens

    #
    def tokenize_string(self, fileName, lineNum, code):
        """
        Tokenize a string rather than a set of line objects
        :param fileName: The filename the source code came from
        :param lineNum: The original line number of the source code
        :param code:  The string of code to be tokenized
        :return: A list of token objects
        """
        logger = logging.getLogger('VirtualBasic')

        tokens = []
        token_tuples, remainder = self.tokenizer.scan(code)
        if remainder is not None and remainder != "":
            # Uh oh... something didn't tokenize
            logger.error(
                "Syntax error in file {1} at line #{0}:\n{2}\nError at code \"{3}\".".format(fileName, code, lineNum,
                                                                                             code))
            token_count = 0
            logger.error("Parsed tokens on this line")
            for token in token_tuples:
                logger.error("Token: {0}: '{1}' ({2})".format(token_count, token[0], token[1]))
            exit(1)
        for newtoken in token_tuples:
            # Append new topken objects based on token tuples from RE tokenizer
            # Add info from this line of code
            tokens.append(TokenObj(fileName, lineNum, newtoken[0], newtoken[1]))
        return tokens

    def de_tokenize(self, tokens):
        """
         Convert tokens back into program text
        :param tokens: List of tokens to be converted
        :return: String containing detokenized code
        """
        lines = []
        start_line = True  # Indicate we're on a new line of source code
        code = ""
        file_name = ""
        line_num = 0

        for token in tokens:
            if start_line:
                file_name = token.filename
                line_num = token.lineNum
                start_line = False

            if token.tokenID == "EOL":
                code += "\n"
                # End of line, save line
                lines.append(CodeLine(file_name, line_num, code))
                start_line = True
                code = ""
                continue

            # We do not capitalize strings or remarks. Otherwise, everything else
            # is capitalized
            if token.tokenID == "STRING" or token.tokenID == "REMARK":
                code += token.tokenText
            else:
                code += token.tokenText.upper()
        # Include last line if it's not empty
        if code != "":
            lines.append(CodeLine(file_name, line_num, code))
        return lines

    #
    def get_nth_left_nonspace_token_obj(self, tokens, index, n):
        """
        Grab the nth non-space token to the left of a point
        in a list of tokens
        :param tokens: List of tokens to operate on
        :param index: The location in the list to search from
        :param n: number of tokens back to find
        :return: The token object found, if any. Returns None if no token matches.
        """
        logger = logging.getLogger('VirtualBasic.get_nth_left_nonspace_token_obj')
        if len(tokens) - n <= 0:
            # trivial case: Want to go further than is possible.
            logger.warning('File {0} line {1}: Tried to advance beyond start of code finding {2} tokens to '
                           'left of {3}.'.format(tokens[index].filename, tokens[index].lineNum, n,
                                                 tokens[index].tokenText))
            return None
        # index = n
        token_count = 0
        # Skip over any whitespace
        while token_count < n:
            while abs(index) <= len(tokens) and tokens[index].tokenID == "WHITESPACE":
                index -= 1
            if abs(index) > len(tokens):
                # Oops, we fell off the front of the list
                logger.warning('Somehow managed to advance past end of code while going left.')
                return None, 0
            else:
                # Must have hit a non-whitespace
                token_count += 1
                if token_count < n:
                    index -= 1
        return (tokens[index], index)

    @staticmethod
    def get_nth_right_nonspace_token_obj(tokens, n):
        """
        Grab the nth non-space token to the right of the start of list of tokens
        :param tokens: List of toeksn to search
        :param n: Number of tokens to right to search
        :return: Token object found, if any. Returns None if no token found.
        """

        logger = logging.getLogger('VirtualBasic.get_nth_right_nonspace_token_obj')
        if n > len(tokens):
            # trivial case: Want to go further than is possible.
            logger.warning('File {0} line {1}: Attempt to advance beyond start of code.'.format(
                tokens[0].filename, tokens[0].lineNum
            ))
            return None
        index = 0
        token_count = 0
        # Skip over any whitespace
        while token_count < n:
            while index < len(tokens) and tokens[index].tokenID == "WHITESPACE":
                index += 1
            if index == len(tokens):
                # Oops, we fell off the end of the list
                return None
            else:
                # Must have hit a non-whitespace
                token_count += 1
                # Advance to next token if we haven't found what we want
                if token_count < n:
                    index += 1
        return tokens[index]

    def get_left_var_ref(self, tokens):
        """get the rightmost variable reference in a token list.
        :param tokens: The list of tokens to get varref from.
        :rtype : object
        :return: a variable ref, or a fully-qualified array ref
        """
        logger = logging.getLogger('VirtualBasic')
        index = len(tokens) - 1

        # Skip any whitespace
        while tokens[index].tokenID == "WHITESPACE":
            index -= 1

        # Must get either a variable ref or a right paren
        if tokens[index].tokenID not in ("INTVAR", "IDENTIFIER", "STRINGVAR", "RPAREN"):
            # Nothing found.
            logger.warning("File {0} line {1}: Found non-variable ({3}) when expecting variable reference.".format(
                tokens[index].fileName, tokens[index].lineNum, tokens[index].tokenText))
            return None, 0
        if tokens[index].tokenID == "RPAREN":
            # Need to see if the paren represents an array reference or not.
            # Need to get the full array ref
            (array_ref, newindex) = self.find_matching_paren_or_array_ref_left(tokens, index - 1)
            array_ref.append(tokens[index])
            # print("returning array ref: " + self.pp.pformat(array_ref))
            return array_ref, newindex
        else:
            # Just return the variable ref
            # print("returning variable ref: " + self.pp.pformat([tokens[index]]) + ' index: ' + str(index - 1))
            return [tokens[index]], index - 1

    def find_matching_paren_or_array_ref_left(self, tokens, index):
        """
        Return array ref or exit with error if we find matching left paren.
        :param tokens: Tokens to search for the paren
        :param index: Where in the token list to start searching
        :return: The array ref and the index of the matching paren. Not finding the array def causes a fatal error.
        """
        logger = logging.getLogger('VirtualBasic')

        r_paren_count = 0  # Track # of right parents we meet.
        array_ref = []  # Holds the array reference, assuming we found one
        # Go backwards until we reach an array ref or left paren that matched the one at the end of the
        while index > 0:
            if tokens[index].tokenID in self.arrayRefs and r_paren_count == 0:
                # Found an array ref.
                array_ref.insert(0, tokens[index])
                return array_ref, index
            elif tokens[index].tokenID in self.arrayRefs:
                r_paren_count -= 1  # Array ref closes out a nested right paren
            elif tokens[index].tokenID == 'LPAREN':
                if r_paren_count == 0:
                    # The right paren matches a bare left paren. Error
                    logger.error("file {0} line {1} : Post increment/decrement on parenthetical expression.".format(
                        tokens[index].filename, tokens[index].lineNum))
                    exit(1)
                else:
                    r_paren_count -= 1  # Closed paren
            elif tokens[index].tokenID == 'RPAREN':
                # Found another right paren... assume nested reference or variable
                r_paren_count += 1
            # Save this token
            array_ref.insert(0, tokens[index])
            index -= 1  # Continue backwards
        # We fell off the front of the code without finding a matching
        # arrayref
        logger.error("Error: could not find a matching array reference for post increment or post decrement operator.")
        exit(1)

    def handle_operators(self):
        """Handles -=, +=, and post decrement and postincrement operators"""
        new_code = []  # We build new list of tokens as we go on
        post_ops = []  # Remember which vars we need to autoincrement at end of statement
        line_count = 1
        logger = logging.getLogger('VirtualBasic')

        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            if token.tokenID == "EOL":
                # Increment line count
                line_count += 1
            if token.tokenID == "PLUSEQUALS" or token.tokenID == "MINUSEQUALS":
                # Need to replace operator with '= <VAR> +'
                (left_sib, left_sib_index) = self.get_left_var_ref(new_code)
                if not left_sib:
                    logger.error("Error: file: {0} line: {1} operator {2} used with non-identifier {3}".format(
                        token.filename, token.lineNum, token.tokenText,
                        self.get_nth_left_nonspace_token_obj(new_code, 0, 1).tokenText))
                    exit(1)
                else:
                    new_code.append(TokenObj(token.filename, token.lineNum, "EQUATE", "="))
                    new_code += left_sib
                    operator = "+" if token.tokenID == "PLUSEQUALS" else "-"
                    new_code.append(TokenObj(token.filename, token.lineNum, "OPERATOR", operator))
            elif token.tokenID == "POSTOP":
                inc_var, prev_token = self.get_left_var_ref(new_code)
                # Error out if postop didn't occur afer a varaible ref.
                # TODO: Extend this to array reference

                if not inc_var:
                    logger.error(
                        "Error: Filename: {0} line #{1} : operator {2} used with non variable or array {3}".format(
                            token.fileName, token.lineNum, token.tokenText))
                    exit(1)

                # Look ahead and behind to determine if this is a standalone reference. If so, we will just put the
                # increment statement here.
                next_token = self.get_nth_right_nonspace_token_obj(self.tokens, 1)
                (second_left_token, prev_token) = self.get_nth_left_nonspace_token_obj(new_code, prev_token, 1)
                if next_token.tokenID in (
                        "STATEMENTSEP", "EOL") and second_left_token is not None and second_left_token.tokenID in [
                    "STATEMENTSEP", "EOL"]:
                    # Yes, so let's do the increment in place here.
                    new_code.append(TokenObj(token.filename, token.lineNum, "EQUATE", "="))
                    new_code += inc_var
                    operator = "+" if token.tokenText == "++" else "-"
                    new_code.append(TokenObj(token.filename, token.lineNum, "OPERATOR", operator))
                    new_code.append(TokenObj(token.filename, token.lineNum, "INTLITERAL", "1"))
                else:
                    # Save var and the operation onto the postOp stack
                    post_ops.append([inc_var, token.tokenText])

            elif token.tokenID == "STATEMENTSEP" or token.tokenID == "EOL":
                # Reached end of line or statement. Need to handle increment
                # or decrements
                for var in post_ops:
                    new_code.append(TokenObj(token.filename, token.lineNum, "STATEMENTSEP", ":"))
                    new_code = new_code + var[0]
                    new_code.append(TokenObj(token.filename, token.lineNum, "EQUATE", "="))
                    new_code = new_code + var[0]
                    operator = "+" if var[1] == "++" else "-"
                    new_code.append(TokenObj(token.filename, token.lineNum, "OPERATOR", operator))
                    new_code.append(TokenObj(token.filename, token.lineNum, "INTLITERAL", "1"))
                # Add the final statement sep or EOL
                new_code.append(token)
                # Clear stack
                post_ops = []
            else:
                # Just add token to output
                new_code.append(token)
                # index += 1
        # Replace old list of tokens with the new
        self.tokens = new_code

    @staticmethod
    def discard_leading_whitespace(tokens):
        """Remove any tokens at start of token list that are whitespace.
        :param tokens: The tokens to remove leading whitespaces from.
        """
        while tokens[0].tokenID == "WHITESPACE":
            tokens.pop(0)

    # Locate function definitions
    def findFunctionDefs(self):
        """
        Collect function definitions.
        Function declarations look like:
            FUNCTION <return Type> <name> (<param type> <param name>, ...)
        """
        logger = logging.getLogger('VirtualBasic')

        new_tokens = []
        curr_func = ""  # Hold name of function we're currently in.
        this_func = None  # The function object of the function we're in
        # Track what types of params and return values we have seen. Need to
        # DIM and define those later.
        have_int_param = False
        have_float_param = False
        have_string_param = False
        have_int_return = False
        have_float_return = False
        have_string_return = False
        # Keep track of whether we are in a function or not.
        in_function = False
        in_var_def = False
        local_var_list = {}  # Hold list of variables defined in the function
        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            for case in switch(token.tokenID):
                # Handle function definition token
                if case('FUNCDEC'):
                    local_var_list = {}  # Clear list of local vars
                    if in_function:
                        # Buh... already in a function definition. No nesting allowed!
                        logger.error(
                            "Error in file {0} line #{1}: Encountered another function definition in function {2}. Missing ENDFUNCTION?".format(
                                token.filename, token.lineNum, curr_func))
                        exit(1)
                    in_function = True

                    # Start of a function.
                    #
                    # First get return type
                    self.discard_leading_whitespace(self.tokens)
                    func_type = self.tokens.pop(0)
                    if not func_type.tokenID in self.varDecTokens:
                        # Not a delcaration. Die
                        logger.error(
                            "Error: in file {0} line #{1}: Cannot declare a function to be of type '{2}'.".format(
                                token.filename, token.lineNum, func_type.tokenText))
                        exit(1)
                    # Now get the function name
                    self.discard_leading_whitespace(self.tokens)
                    func_name = self.tokens.pop(0)
                    name = func_name.tokenText[:-1]  # -1 to discard the (
                    if func_name.tokenID != "FLOATARRAY":
                        logger.error("Error: filename {0} line#{1}: Cannot declare a function with name '{2}'.".format(
                            token.filename, token.lineNum, func_name.tokenText))
                        exit(1)
                    if name in self.funcDefs:
                        logger.error("Error: Filename {0} line #{1}: Function '{2}' has already been defined.".format(
                            token.filename, token.lineNum, func_name.tokenText))
                        exit(1)
                    this_func = FunctionDef(name, func_type.tokenID)
                    self.funcDefs[name] = this_func
                    curr_func = name

                    # Now get the lead paren and parameters
                    self.discard_leading_whitespace(self.tokens)
                    # Track the # of each type of params
                    next_token = self.tokens.pop(0)
                    # Read ParmaType ParamName , triplets until we reach the end
                    while next_token.tokenID != "RPAREN":
                        # Token shold be a type declaration
                        if not next_token.tokenID in self.varDecTokens:
                            logger.error("Error: File: {0} line #{1}: In function declaration " +
                                         "{2}, expected parameter type '{3}'.".format(
                                             token.filename, token.lineNum, func_name.tokenText, next_token.tokenText))
                            exit(1)
                        # Get the parameter name
                        self.discard_leading_whitespace(self.tokens)
                        param_name = self.tokens.pop(0)
                        if param_name.tokenID != "IDENTIFIER":
                            logger.error(
                                "Error: File: {0} line #{1}: In function {2}: Expected a parameter name, got {3}".format(
                                    token.filename, token.lineNum, func_name.tokenText, param_name.tokenText))
                            exit(1)
                        # Set up type-specific stuff

                        this_func.paramName.append(param_name.tokenText)
                        this_func.paramType.append(next_token.tokenID)
                        this_func.totalParamCount += 1
                        # Increment the count of appropriate param type.
                        for case in switch(next_token.tokenID):
                            if case('INTDEC'):
                                this_func.intParams += 1
                                have_int_param = True
                                break
                            if case('FLOATDEC'):
                                this_func.floatParams += 1
                                have_float_param = True
                                break
                            if case('STRINGDEC'):
                                this_func.stringParams += 1
                                have_string_param = True

                        # Get the comma, if there
                        self.discard_leading_whitespace(self.tokens)
                        next_token = self.tokens.pop(0)
                        if next_token.tokenText == ',':
                            self.discard_leading_whitespace(self.tokens)
                            next_token = self.tokens.pop(0)
                        if next_token.tokenID == 'EOL':
                            # Reached end of line before we got a token. You sux Mr./Ms. Programmer!
                            logger.error(
                                "Error in file: {0} line #{1}: function declaration {2}, unexpected end of line (missing closing paren?).".format(
                                    token.filname, token.lineNum, func_name.tokenText))
                            exit(1)

                    # Ok, got the right paren to close out the function. Populate the function definition with the
                    # replacements for the params. Can't do this until we know the total # of
                    # all types of params, since we need know the offset from the
                    # start of the list.

                    # We set up two repalcement values. One is for the function call set up,
                    # which references values above the current parameter pointer.
                    # The second is the parameter references in the function call
                    # itself, which always refers to values below the current 
                    # parameter pointer. This way a function call within a function
                    # body can work the way we expect it.
                    #
                    # repString, what we replace in the function call
                    # refString, what we replace in the function that referes to a param

                    float_param_seen = 0
                    int_param_seen = 0
                    string_param_seen = 0
                    for i in range(this_func.totalParamCount):
                        for case in switch(this_func.paramType[i]):
                            if case('FLOATDEC'):
                                # Come up with replacement text for this param in the
                                # function
                                #
                                getString = "sfFloatParam(sfFloatParamPointer"
                                setString = getString
                                if float_param_seen == this_func.floatParams - 1:
                                    # Last param
                                    getString += ")"

                                else:
                                    # Not last param, have to subtract an offset
                                    getString += "-" + str(this_func.floatParams - 1 - float_param_seen) + ")"
                                this_func.paramGet[this_func.paramName[i]] = getString
                                setString += " + " + str(1 + float_param_seen) + ")"
                                this_func.paramSet[this_func.paramName[i]] = setString
                                float_param_seen += 1
                                break
                            if case('INTDEC'):
                                getString = "siIntParam(siIntParamPointer"
                                setString = getString
                                if int_param_seen == this_func.intParams - 1:
                                    # Last param
                                    getString += ")"
                                else:
                                    # Not last param, have to subtract an offset
                                    getString += "-" + str(this_func.intParams - 1 - int_param_seen) + ")"
                                this_func.paramGet[this_func.paramName[i]] = getString
                                setString += " + " + str(1 + int_param_seen) + ")"
                                this_func.paramSet[this_func.paramName[i]] = setString
                                int_param_seen += 1
                                break
                            if case('STRINGDEC'):
                                getString = "ssStringParam(ssStringParamPointer"
                                setString = getString
                                if string_param_seen == this_func.stringParams - 1:
                                    # Last param
                                    getString += ")"
                                else:
                                    # Not last param, have to subtract an offset
                                    getString += "-" + str(this_func.stringParams - 1 - string_param_seen) + ")"
                                this_func.paramGet[this_func.paramName[i]] = getString
                                setString += " + " + str(1 + string_param_seen) + ")"
                                this_func.paramSet[this_func.paramName[i]] = setString
                                string_param_seen += 1
                                break
                    # Done setting up function object

                    # Add label for function
                    new_tokens.append(TokenObj(token.filename, token.lineNum, 'LINELABELDEF', '_' + curr_func))
                    new_tokens.append(TokenObj(token.filename, token.lineNum, 'EOL', "\n"))

                    # End of function case
                    break

                # Handle function end token
                if case('FUNCEND'):
                    # End of function... add in end code
                    # Add label for end of function
                    new_tokens.append(TokenObj(token.filename, token.lineNum, 'LINELABELDEF', '_' + curr_func + "-end"))
                    new_tokens.append(TokenObj(token.filename, token.lineNum, 'EOL', "\n"))

                    new_tokens.append(TokenObj(token.filename, token.lineNum, 'RETURN', "RETURN"))
                    new_tokens.append(TokenObj(token.filename, token.lineNum, 'EOL', "\n"))
                    in_function = False
                    break

                # Handle return token. If inside a function definition, the return
                # must return a value.
                if case('RETURN'):
                    # See if this is a return in a function
                    retVar = ""
                    if in_function:
                        # OK, need to figure out what to return.
                        # Get the next token. It should be a return value
                        # or literal

                        self.discard_leading_whitespace(self.tokens)
                        # retVal = self.get_remainder_of_statement_or_line(self.tokens)
                        for case in switch(this_func.retType):
                            if case("INTDEC"):
                                retVar = "riReturnIntValue"
                                have_int_return = True
                                break
                            if case("FLOATDEC"):
                                retVar = "rfReturnFloatValue"
                                have_float_return = True
                                break
                            if case("STRINGDEC"):
                                retVar = "rsReturnStringValue"
                                have_string_return = True
                                break
                        # Insert returnVar = <statement>
                        new_tokens += self.tokenize_string(token.filename, token.lineNum, retVar + " = ")
                        # new_tokens += retVal
                        # Insert the goto that jumps to end of function after
                        # this statement's end
                        if not self.insert_next_statement(self.tokens, ": GOTO @" + curr_func + "-end"):
                            # Problem inserting the return statement
                            logger.error(
                                "Error attemptint to process RETURN statement in function {0}".format(this_func.name))
                            exit(1)
                        # Done with the return.
                        break
                    else:
                        new_tokens.append(token)
                        break

                # For any variable reference, we need to see if it is a
                # parameter in a function. If so, we replace it with the 
                # previously-defined parameter reference. We also check to see if the
                # variable has been defined within the function. If so, we prepend its name

                if case('IDENTIFIER'):
                    if in_function:
                        # See if the variable is a parameter reference that needs
                        # replacing
                        if token.tokenText in this_func.paramName:
                            # Yes, it's a param. Replace it.
                            # We need to tokenize the parameter value and append
                            paramTok = self.tokenize_string(token.filename, token.lineNum,
                                                            this_func.paramGet[token.tokenText])
                            new_tokens += paramTok
                            break
                        # If we are in a variable definition, we want to rename the variable and save it.
                        if in_var_def:
                            newName = this_func.name + "_" + token.tokenText
                            local_var_list[token.tokenText] = newName
                            token.tokenText = newName
                        elif token.tokenText in local_var_list:
                            token.tokenText = local_var_list[token.tokenText]
                        new_tokens.append(token)
                        break

                # Set flag if we are in a variable def.
                if case('INTDEC'): pass
                if case('FLOATDEC'): pass
                if case('STRINGDEC'):
                    in_var_def = True
                    new_tokens.append(token)
                    break

                # reaching EOL, : , or =  always ends a variable definition
                if case('EOL'): pass
                if case('STATEMENTSEP'): pass
                if case('EQUATE'):
                    in_var_def = False
                    new_tokens.append(token)
                    break

                # defaul case, just append token
                if case():
                    new_tokens.append(token)

        # Define arrays for parameters, and declare return values
        prefixTokens = self.declare_params_and_returns(have_int_param, have_float_param, have_string_param,
                                                       have_int_return, have_float_return, have_string_return)

        # Update code
        self.tokens = prefixTokens + new_tokens

    def dump_tokens(self, tokens):
        """
        Simple debug utility function to print structure of the token list
        :param tokens: list of tokens to print
        :return: nothing
        """
        logger = logging.getLogger('VirtualBasic')
        for token in tokens:
            if isinstance(token, TokenObj):
                logger.debug("TokenID: {0} Text: {1} File: {2} Line #{3}".format(
                    token.tokenID, token.tokenText, token.filename, token.lineNum
                ))
            else:
                logger.debug("***Non-token: {0}".format(self.pp.pformat(token)))

    @staticmethod
    def print_token_stream(tokens):
        """ Print the code from a list of tokens
        :param tokens: List of tokens containing the code to print
        :return: Nothing. Prints code to stdout.
        """
        logger = logging.getLogger('VirtualBasic')
        code = ""
        for token in tokens:
            code += token.tokenText
        logger.debug(code)

    def insert_next_statement(self, tokens, statement):
        """ Insert a statement as the next statement in a token list.
        This is used to insert a statement after the statement being
        processed currently.
        :rtype : Boolean
        :param tokens: The list of tokens to insert into
        :param statement: The statement as a string to insert
        :return: True if success, False if failure.
        """

        index = 0
        # Find start of next statement/line
        while tokens[index].tokenID not in ['STATEMENTSEP', 'EOL']:
            index += 1
            if index == len(tokens):
                # Fell off end of code.
                return False
        # OK, splice the code into the token stream
        tokens[index:index] = self.tokenize_string(tokens[index - 1].filename,
                                                   tokens[index - 1].lineNum, statement)
        return True

    def get_remainder_of_statement_or_line(self, tokens):
        """ Pop everything from list until either EOF or statement separator. Effectively
            this pops everything from the statement that starts the token list.
        :param tokens: The list of tokens to pop. As a side effect, this list will start
                       with a statement separator or newline on return.
        :return: a list of the tokens that were popped off the front of the list
        """
        ret = []
        while len(tokens) and tokens[0].tokenID not in ['EOL', 'STATEMENTSEP']:
            ret.append(tokens.pop(0))
        return ret

    def declare_params_and_returns(self, int_param, float_param, string_param, int_return, float_return, string_return):
        """
        Declare the arrays used for parameters and return values in the VB++ code.
        :param int_param: Max depth of integer parameter array
        :param float_param: max depth of the float parameter array
        :param string_param: max depth of the string parameter array
        :param int_return: max depth of the integer return array
        :param float_return: max depth of float return array
        :param string_return: max depth of the sting return array
        :return: a list of tokens for the VB++ code to declare the arrays.
        """
        prefixCode = ""
        if int_param:
            maxIntParams = 25
            if 'MAXINTPARAMS' in self.defines:
                maxIntParams = self.defines['MAXINTPARAMS']
            prefixCode += "integer siIntParam(" + str(maxIntParams) + ")\n"
            prefixCode += "float siIntParamPointer\n"
        if float_param:
            maxFloatParams = 25
            if 'MAXFLOATPARAMS' in self.defines:
                maxFloatParams = self.defines['MAXFLOATPARAMS']
            prefixCode += "float sfFloatParam(" + str(maxFloatParams) + ")\n"
            prefixCode += "float sfFloatParamPointer\n"
        if string_param:
            maxStringParams = 25
            if 'MAXSTRINGPARAMS' in self.defines:
                maxStringParams = self.defines['MAXSTRINGPARAMS']
            prefixCode += "string ssStringParam(" + str(maxStringParams) + ")\n"
            prefixCode += "float ssStringParamPointer\n"
        if int_return:
            prefixCode += 'integer riReturnIntValue\n'
            maxIntReturns = 5
            if 'MAXINTRETURNS' in self.defines:
                maxIntReturns = self.defines['MAXINTRETURNS']
            prefixCode += "integer ihReturnIntHeap(" + str(maxIntReturns) + ")\n"
        if float_return:
            prefixCode += 'float rfReturnFloatValue\n'
            maxFloatReturns = 5
            if 'MAXFLOATRETURNS' in self.defines:
                maxFloatReturns = self.defines['MAXFLOATRETURNS']
            prefixCode += "float fhReturnFloatHeap(" + str(maxFloatReturns) + ")\n"
        if string_return:
            prefixCode += 'string rsReturnStringValue\n'
            maxStringReturns = 5
            if 'MAXSTRINGRETURNS' in self.defines:
                maxStringReturns = self.defines['MAXSTRINGRETURNS']
            prefixCode += "string shReturnStringHeap(" + str(maxStringReturns) + ")\n"
        # tokenize the autogenerated code
        if prefixCode != "":
            prefixCode = "REM autogenerated array definitions for function parameters\n" + prefixCode
        prefixTokens = self.tokenize_string("VirtualBasic++ Generated", 0, prefixCode)
        return prefixTokens

    def replace_function_calls(self):
        """Replace the @name(param1, param2, ...) with marshalling code
           that loads param values in the proper array, gosubs to the
           function, then saves the return value off into a variable"""

        new_code = []  # holds processed code

        # Hold the number of function calls we'll see in this statement. Used
        # to determing if we have to use an array to hold the return values
        # or if we can just use the return variable directly.

        logger = logging.getLogger('VirtualBasic')

        int_rets = 0
        float_rets = 0
        string_rets = 0

        # Track how many return values we've processed
        int_rets_handled = 0
        float_rets_handled = 0
        string_rets_handled = 0
        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            # Just append anything that's not a function call
            if token.tokenID == 'STATEMENTSEP' or token.tokenID == 'EOL':
                # get the count of function call return types in upcoming statement.
                (int_rets, float_rets, string_rets) = self.find_num_function_calls_in_statement(self.tokens)
                new_code.append(token)
                int_rets_handled = 0
                float_rets_handled = 0
                string_rets_handled = 0
                continue

            # Just append anything that's not a function call
            if token.tokenID != 'FUNCTIONCALL':
                new_code.append(token)
                continue

            # Handling a function call.
            func_name = token.tokenText[1:-1]  # trim the (
            if func_name not in self.funcDefs:
                # Oops. Function doesn't exist. Die
                logger.debug("Error in file {0} on line #{1}: function '{2}' has not been defined.".format(
                    token.filename, token.lineNum, func_name))
                exit(1)
            my_func = self.funcDefs[func_name]
            params = self.get_param_list(self.tokens)

            func_setup = []

            # Create assignment statements for each parameter.
            for parm in my_func.paramName:
                # Get the array ref code and append an equal sign
                assing_str = " " + my_func.paramSet[parm] + " = "
                # Tokenize and append to setup tokens
                func_setup += self.tokenize_string(token.filename, token.lineNum, assing_str)
                # Get the expression for the parameter and append it
                func_setup += params.pop(0)
                # Append a colon to separate the statement
                func_setup.append(TokenObj(token.filename, token.lineNum, 'STATEMENTSEP', ':'))

            pointer_str = ""
            pointer_dec_str = ""
            # set the pointers for the function call entries
            if my_func.intParams > 0:
                pointer_str += "siIntParamPointer += " + str(my_func.intParams) + " : "
                pointer_dec_str += "siIntParamPointer -= " + str(my_func.intParams) + " : "
            if my_func.floatParams > 0:
                pointer_str += "sfFloatParamPointer += " + str(my_func.floatParams) + " : "
                pointer_dec_str += "sfFloatParamPointer -= " + str(my_func.floatParams) + " : "
            if my_func.stringParams > 0:
                pointer_str += "ssStringParamPointer += " + str(my_func.stringParams) + " : "
                pointer_dec_str += "ssStringParamPointer -= " + str(my_func.stringParams) + " : "

            # Save the pointer setup
            func_setup += self.tokenize_string(token.filename, token.lineNum, pointer_str)

            # Finally, append the gosub.
            func_setup += self.tokenize_string(token.filename, token.lineNum, "GOSUB @" + my_func.name + " : ")

            # Decrement the parameter pointer to free the array space
            func_setup += self.tokenize_string(token.filename, token.lineNum, pointer_dec_str)

            # Need to see if we have to save off the return value into an array.
            # this has to happen when we have multiple function calls in the
            # statement that return the same data type.
            for case in switch(my_func.retType):
                if case("INTDEC"):
                    if int_rets > 1:
                        # Yup. Multiple integer return vars. Need to save off the
                        # return value into an array
                        func_setup += self.tokenize_string(token.filename, token.lineNum,
                                                           " ihReturnIntHeap({0}) = riReturnIntValue :".format(
                                                               int_rets_handled))
                        # Save the string to use to access the value in the calling expression
                        value_ref = " ihReturnIntHeap({0}) ".format(int_rets_handled)
                        int_rets_handled += 1  # Increase count of int return vals
                    else:
                        # Otherwise, we just use the return variable to access the value
                        value_ref = " riReturnIntValue "
                    break
                if case("FLOATDEC"):
                    if float_rets > 1:
                        # Yup. Multiple float return vars. Need to save off the
                        # return value into an array
                        func_setup += self.tokenize_string(token.filename, token.lineNum,
                                                           " fhReturnFloatHeap({0}) = rfReturnFloatValue :".format(
                                                               float_rets_handled))
                        # Save the string to use to access the value in the calling expression
                        value_ref = " fhReturnFloatHeap({0}) ".format(float_rets_handled)
                        float_rets_handled += 1  # Increase count of int return vals
                    else:
                        # Otherwise, we just use the return variable to access the value
                        value_ref = " rfReturnFloatValue "
                    break
                if case("STRINGDEC"):
                    if string_rets > 1:
                        # Yup. Multiple string return vars. Need to save off the
                        # return value into an array
                        func_setup += self.tokenize_string(token.filename, token.lineNum,
                                                           "shReturnStringHeap({0}) = rsReturnStringValue :".format(
                                                               string_rets_handled))
                        # Save the string to use to access the value in the calling expression
                        value_ref = " shReturnStringHeap({0}) ".format(string_rets_handled)
                        string_rets_handled += 1  # Increase count of int return vals
                    else:
                        # Otherwise, we just use the return variable to access the value
                        value_ref = " rsReturnStringValue "
                    break
                if case():
                    # Should never get here...
                    logger.error("Error: unknown function return type {0}".format(my_func.retType))
                    exit(1)

            # Now we have a complete set of statements to set up function call.
            # So, add it before the current statement.
            new_code = self.insert_before_last_statement(new_code, func_setup)

            # We only insert a value reference if the function call is part of
            # an expression. If the function call is the only piece of the
            # expression (i.e. nothing by a statementsep or newline before and after the
            # function call) then we don't even put the statement ref in.
            if self.other_tokens_in_statement(new_code, self.tokens):
                # Insert the function reference
                # print("Inserting var ref " + value_ref)
                new_code += self.tokenize_string(token.filename, token.lineNum, value_ref)
        self.tokens = new_code

    @staticmethod
    def other_tokens_in_statement(back, forward):
        """ Search backwards and forwards to see if there is
            any other token type in this statement.

        :param back: list of tokens before current token
        :param forward: list of tokens after current token

        :return: True if there is some other token
                 False if nothing but whitespace before reaching an EOL or STATEMENTSEP"""

        # logger = logging.getLogger('VirtualBasic')
        back_index = len(back) - 1

        while back[back_index].tokenID == 'WHITESPACE':
            back_index -= 1
        if back[back_index].tokenID not in ['EOL', 'STATEMENTSEP']:
            return True

        forward_index = 0
        while forward[forward_index].tokenID == 'WHITESPACE':
            forward_index += 1

        if forward[forward_index].tokenID not in ['EOL', 'STATEMENTSEP']:
            return True

        # If we reach here, then no other token was found
        return False

    def find_num_function_calls_in_statement(self, tokens):
        """ Given a stream of tokens, look through the current statement to
            find the number of all types of function calls
        :param tokens: List of tokens to search
        """
        logger = logging.getLogger('VirtualBasic')

        index = 0
        int_count = 0
        float_count = 0
        string_count = 0
        while index < len(tokens):
            if tokens[index].tokenID == 'FUNCTIONCALL':
                # Find the return type of this function call
                func_name = tokens[index].tokenText[1:-1]
                if not func_name in self.funcDefs:
                    # This function isn't defined.
                    logger.error("Error in file {0} starting on line {1}: Call to undefined function '{2}'.".format(
                        tokens[index].filename, tokens[index].lineNum, func_name))
                    exit(1)
                for case in switch(self.funcDefs[func_name].retType):
                    if case("INTDEC"):
                        int_count += 1
                        break
                    if case("FLOATDEC"):
                        float_count += 1
                        break
                    if case("STRINGDEC"):
                        string_count += 1
                        break
            elif tokens[index].tokenID == 'STATEMENTSEP' or tokens[index].tokenID == 'EOL':
                return int_count, float_count, string_count
            index += 1
        # Reached end of tokens, return what we have
        return int_count, float_count, string_count

    def insert_before_last_statement(self, tokens, insert):
        """ Find last statement separator in token list and insert tokens before it
        :param tokens: List of tokens to insert into
        :param insert: The tokrns to insert
            """
        insert_loc = 0
        for index in range(len(tokens) - 1, 0, -1):
            if tokens[index].tokenID == "STATEMENTSEP" or tokens[index].tokenID == "EOL":
                insert_loc = index + 1
                break
        return tokens[:insert_loc] + insert + tokens[insert_loc:]

    def get_param_list(self, tokens):
        """
        Get the list of param values from a function call. The values can
        be any exoression. They cannot be another function call, however.
        :param tokens: The list of tokens to be searched for a parameter list
        :return: The list of tokens making up the function parameters
        """

        logger = logging.getLogger('VirtualBasic')
        start_tok = tokens[0]
        params = []
        curr_param = []
        done = False
        nested_parens = 0
        while not done:
            if len(tokens) == 0:
                # Ran out of tokens. Probably a missing right paren someplace
                logger.error("Error in file {0} starting on line {1}: runaway function call.".format(
                    start_tok.filename, start_tok.lineNum))
                exit(1)

            token = tokens.pop(0)
            for case in switch(token.tokenID):
                if case("RPAREN"):
                    if nested_parens == 0:
                        # Done with everything
                        params.append(curr_param)  # Add last expression to list
                        done = True
                    # Closing paren within an expression
                    else:
                        nested_parens -= 1
                        curr_param.append(token)
                    break
                if case("LPAREN", "FLOATARRAY", "INTARRAY", "STRINGARRAY"):
                    # Set nesting level so we expect another right paren before close of
                    # the function call
                    nested_parens += 1
                    curr_param.append(token)
                    break
                # For commas, add the current expression to list of params
                if case('PUNCTUATION'):
                    params.append(curr_param)
                    curr_param = []
                    break
                # Anything other than comma or closing paren
                if case():
                    # See if this is valid to have in an expression in
                    # a parameter list
                    if not token.tokenID in self.allowedInParameterExp:
                        logger.error(
                            "Error in file {0} line #{1}: Illegal element type {3} in call parameter list '{2}'".format(
                                token.filename, token.lineNum, token.tokenText, token.tokenID))
                        exit(1)
                    # OK to have, so add to the current parameter
                    curr_param.append(token)
                    break
        logger.debug("\n\n\n\nReturning parameter call list: " + self.pp.pformat(params))
        return params

    @staticmethod
    def extract_to_token_type(tokens, token_type):
        """ Pop tokens off left end of token list until
            we get to a specific token. Leaves that token
            on the list. Returns the list of extracted tokens
        :type token_type: String
        :param tokens: The list of tokens to process
        :param token_type: The type of token to extract to
        :return: the tokens popped off the list up to (but not including) the token that matchde tokenType
           """

        ret_arr = []
        while not (tokens[0].tokenID == token_type) and len(tokens) > 0:
            ret_arr.append(tokens.pop(0))
        # Either ran out of tokens or found the one we want
        if len(tokens) == 0:
            return None
        else:
            return ret_arr

    @staticmethod
    def extract_to_closing_right_paren(tokens):
        """Pop tokens off token list until we reach
            an unmatched right paren ) 
        :param tokens: List of tokens to process
        """
        ret_arr = []
        l_parens = 0  # Track any nested parens

        token = tokens.pop(0)
        while not (token.tokenID == 'RPAREN' and l_parens == 0):
            ret_arr.append(token)
            if token.tokenID == 'RPAREN':
                # Must match a left paren
                l_parens -= 1
            if token.tokenID == 'LPAREN':
                # Must match a left paren
                l_parens += 1
            if len(tokens) == 0:
                # D'oh! ran out of tokens! Error!
                return None
            token = tokens.pop(0)
        ret_arr.append(token)  # Add on closing paren
        return ret_arr

    def find_variable_defs(self, tokens):
        """
        Harvest the variable definitions from source code. Adds DIM statements
        for any array declarations.
        :rtype : List
        :param tokens: VB++ token list to be search for variables.
        :return: new set of VB++ tokens and the list of declared variables.
        """
        logger = logging.getLogger('VirtualBasic')

        new_tokens = []  # Hold list of tokens after we have processed definitions
        dec_var_list = {}
        line_count = 1
        in_func = False
        func_name = ""
        while len(tokens) > 0:
            token = tokens.pop(0)
            # if token.tokenID == "SCOPEDEC":
            # Local var definition. We don't handle that, so skip to the next statement
            # new_tokens.append(token)
            # skippingStatement = True
            if token.tokenID == "EOL" or token.tokenID == "STATEMENTSEP":
                # Reached end of statement, stop skipping if we were
                new_tokens.append(token)
                # skippingStatement = False
                if token.tokenID == "EOL":
                    line_count += 1

            # FIXME: this will never work.. the function defs are already gone by the time we process
            # VARS. We need to move this into the findFunctionDefs method.
            # FIXME: is this resolved? Not clear, but adding function prefix to vars seems to work...
            elif token.tokenID == "FUNCDEC":
                # For functions, we prepend the name of the function to avoid variable name collisions
                # print("Func def found while scaning for vars")
                in_func = True
                new_tokens.append(token)
                next_token = tokens.pop(
                    0)  # FIXME: Huh? What? This is never used? Or is this popping the assumed whitespace?
                self.discard_leading_whitespace(self.tokens)
                func_type = self.tokens.pop(0)  # FIXME: Verify that this is a valid return type?
                new_tokens.append(func_type)
                # Now get the function name
                self.discard_leading_whitespace(self.tokens)  # FIXME: should we discard anything?
                func_name_tok = self.tokens.pop(0)
                func_name = func_name_tok.tokenText
            elif token.tokenID == "FUNCEND":
                in_func = False
                func_name = ""
                new_tokens.append(token)
            elif token.tokenID in self.varDecTokens:
                # Have a variable declaration keyword
                done = False
                vars_in_line = []  # Hold the vars on this line in case we need to init them to
                # a value
                while not done:
                    # Skip whitespace
                    while tokens[0].tokenID == "WHITESPACE":
                        tokens.pop(0)
                    var_name = tokens.pop(0)  # Get (first?) variable ref
                    # print("{0} - {1}".format(var_name.tokenID, var_name.tokenText))

                    # Remove upperase and any whitespace before a (
                    var_name.tokenText = var_name.tokenText.upper().replace(" ", "")
                    if in_func:
                        # In functions, prepend the name of the function with an underscore
                        # print("Changing local var from {0} to {1}".format(var_name.tokenText, func_name + "_" + var_name.tokenText))
                        var_name.tokenText = func_name + "_" + var_name.tokenText
                    if not var_name.tokenID in self.idTokens and not var_name.tokenID in self.arrayRefs:
                        # Not a valid variable reference
                        logger.error("Error in file {0} line #{1}: variable declaration {2}"
                                     "followed by non-variable reference {3}.".format(
                            token.filename, token.lineNum, token.tokenText, var_name.tokenText))
                        exit(1)

                    # Append to list of vars we have found
                    vars_in_line.append(var_name)
                    # save the type of the variable for later
                    var_type = token.tokenID.upper()
                    # See if we have a variable or array def. If it's an array, we need to drop a DIM here
                    # and the variable reference for applesoft's sake
                    if var_name.tokenID in self.arrayRefs:
                        new_tokens.append(TokenObj(token.filename, token.lineNum, "KEYWORD", "DIM"))
                        new_tokens.append(TokenObj(token.filename, token.lineNum, "WHITESPACE", " "))
                        new_tokens.append(var_name)
                        # Handle array dimension. Grab every token up to the closing )
                        sub = self.extract_to_closing_right_paren(tokens)
                        if sub is None:
                            # Could not find closing paren. Error out
                            logger.error(
                                "Error in file {0} line #{1}: Could not find closing paren for array {2}.".format(
                                    token.filename, token.lineNum, var_name.tokenText))
                            exit(1)
                        new_tokens += sub
                        new_tokens.append(TokenObj(token.filename, token.lineNum, "STATEMENTSEP", ":"))

                        # Change type to an array type
                        var_type = token.tokenID.upper() + "ARRAY"
                    # Add variable def to list of variables
                    if var_name.tokenText in dec_var_list:
                        # Variable already defined
                        logger.error("Error in file {0} line #{1}: Variable \"{2}\" has already been defined.".format(
                            token.filename, token.lineNum, var_name.tokenText))
                        exit(1)

                    dec_var_list[var_name.tokenText] = {
                        'name': var_name.tokenText, 'type': var_type,
                        'linenum': token.lineNum, 'filename': token.filename
                    }

                    # Peek ahead to see if we have a comma (for multiple definitions of the same type)
                    while tokens[0].tokenID == "WHITESPACE":
                        new_tokens.append(tokens.pop(0))
                    if tokens[0].tokenID == "PUNCTUATION":
                        # Yup. Pop it and continue loop
                        tokens.pop(0)
                    elif tokens[0].tokenID == "EQUATE":
                        tokens.pop(0)
                        # Have value assignments. This ends the variable defintion. Go insert assignments
                        expression = self.get_remainder_of_statement_or_line(tokens)
                        new_tokens = self.insert_initial_values(new_tokens, vars_in_line, expression)
                        done = True
                    else:
                        # Not continuing, so end of definition
                        done = True
            else:
                # Not a variable def and not some special case... Just append
                new_tokens.append(token)
        tokens = new_tokens
        # print("Declared Variables")
        # self.pp.pprint(dec_var_list)
        return new_tokens, dec_var_list

    @staticmethod
    def insert_initial_values(new_tokens, vars_in_line, expression):
        """
        Add value assignments where variables were declared with an initial value.
        :param new_tokens: The current token stream up to the point where we need to insert the variables
        :param vars_in_line: The list of variables to assign a value
        :param expression: The expression to assign to all of the vars
        :return: Token stream with initializations added
        """

        # Add leading newline if we didn't end last on a newline or statement sep.
        if new_tokens[-1].tokenID != "EQUATE" and new_tokens[-1].tokenID != 'STATEMENTSEP':
            new_tokens.append(TokenObj(vars_in_line[0].filename, vars_in_line[0].lineNum, 'EOL', "\n"))
        file_name = "unknown"  # Will (always?) be overwritten
        line_num = 0
        for variable in vars_in_line:
            # Insert <varliable> = <expression> for each variable in declaration
            file_name = variable.filename  # Save filename and line # for later
            line_num = variable.lineNum
            new_tokens.append(variable)
            new_tokens.append(TokenObj(variable.filename, variable.lineNum, 'EQUATE', "="))
            new_tokens = new_tokens + expression
            new_tokens.append(TokenObj(variable.filename, variable.lineNum, 'STATEMENTSEP', ":"))
        # Wipe out last inserted statementset, replace with EOL
        new_tokens.pop()
        new_tokens.append(TokenObj(file_name, line_num, 'EOL', "\n"))
        return new_tokens

    #
    def find_undef_variables(self, tokens):
        """
        Locate variables that aren't defined. These are treated as "native" Applesoft variables. That is unless
        STRICT has been defined, in which case undefined vars are an error.
        :param tokens: List of that make up the program.
        :return: list of undefined variables.
        """
        logger = logging.getLogger('VirtualBasic')

        undef_vars = {}
        defvar_names = self.decVarList.keys()
        for token in tokens:
            if token.tokenID in self.idTokens or token.tokenID in self.arrayRefs:
                if not token.tokenText.upper().replace(" ", "") in defvar_names and not token.tokenText.upper().replace(
                        " ", "") in undef_vars:
                    # Not seen this varname before.
                    # If STRICT has been defined and we have undefined variables, error out
                    if "STRICT" in self.defines:
                        logger.error(
                            "File {0} Line {1}: Undefined variable {2} of type {3} with STRICT enabled.".format(
                                token.filename,
                                token.lineNum,
                                token.tokenText,
                                token.tokenID))
                        exit(1)
                    # Save unknown varname.
                    undef_vars[token.tokenText.upper().replace(" ", "")] = VarObj(
                        token.tokenText.upper().replace(" ", ""), token.tokenID, token.lineNum, token.filename,
                        True
                    )
                    logger.warning("File {0} Line {1}: use of undeclared variable {2}.".format(token.filename,
                                                                                               token.lineNum,
                                                                                               token.tokenText))
        return undef_vars

    def get_predef_apl_varnames(self, predefvars):
        """ Create a reverse lookup dictionary that links applesoft varnames to their definitions"""
        varnames = {}
        for var in predefvars:
            varnames[predefvars[var]['asoftvar']] = var
        return varnames

    def reserve_native_varnames(self, undef_vars):
        """ Given a list of undefined var tokens, produce a dictionary of reserved Applesoft variable names
        :param undef_vars: List of undefined variable tokens.
        :return: List of reserved Applesoft variables already used in the code.
        """
        logger = logging.getLogger('VirtualBasic')
        reserved_vars = {}
        for variable in undef_vars.keys():
            # Get variable type
            var_type = undef_vars[variable]
            trunc_var = variable
            # If array reference, string rightmost char to get rid
            # of paren
            if var_type in self.arrayRefs:
                trunc_var = trunc_var[:-1]

            # Trim rightmost character if not a float type
            if var_type != "IDENTIFIER" and var_type != "FLOATARRAY":
                trunc_var = trunc_var[:-1]

            # Don't need to record which variable type this is... we just need
            # to note that the variable name is taken so we can avoid it.

            # It is always an error to use a undeclared var that collides with
            # a variabled defined in the external variable file
            if self.havePreDefs:
                if trunc_var in self.predefaplvarsnames:
                    logger.debug(
                        "Error: undeclared variable {0} already defined in pre-defined variable file {1} (".format(
                            variable,
                            ))
                    exit(1)
            reserved_vars[trunc_var] = var_type
        return reserved_vars

    @staticmethod
    def int_to_var_name(value):
        """
        Given an integer value, return a string containing a proposed
        Applesoft variable name. We don't bother with using letterNumber combos
        since generating those is harder
        :rtype : basestring
        :param value: Integer value to
        :return: a variable name
        """
        if value < 26:
            return chr(65 + value)
        else:
            firstchar, secondchar = divmod(value, 26)
            return chr(65 + firstchar) + chr(65 + secondchar)

    def add_predefs_to_reserved_vars(self):
        """
        Add variables from predef file to the list of currenlt-assigned vars.
        """
        self.reservedVars = self.reservedVars + self.a

    def assign_names_to_defvars(self):
        """
        Map defined varables to Applesoft names
        :return:
        """
        logger = logging.getLogger('VirtualBasic')
        # Need to find out if we are using a file to save variable defs. This is needed
        # for things like chaining VirtualBasic++ programs.
        varcount = 1
        assigned_vars = {}
        for variable in self.decVarList:
            # See if we already have a Applesft name for this var
            if self.decVarList[variable].has_key('asoftvar'):
                # It does. Skip it
                continue

            varname = ""
            vartype = self.decVarList[variable]['type']

            # See if the variable is already in the pre-defined list. If so, get its
            # assignment.
            if self.havePreDefs:
                if variable in self.predefvars:
                    if self.predefvars[variable]['type'] != vartype:
                        logger.error(
                            "Error: variable {0} declared as type {1} on line {2} of file {3} conflicts with the definition of type {4} on line {5} of file {6}".format(
                                variable, vartype, self.decVarList[variable]['linenum'],
                                self.decVarList[variable]['filename'], self.predefvars[variable]['type'],
                                self.predefvars[variable]['linenum'], self.predefvars[variable]['filename']
                            ))
                        exit(1)
                    varname = self.predefvars[variable]['asoftvar']
                    logger.debug("Found pre-assigned applesoft var '{0}' for variable '{1}'".format(varname, variable))

            # If no predef file or the file didn't have an entry, choose a name
            if varname == "":
                # First try to truncate var to first letter
                if not variable[0] in self.reservedVars:
                    varname = variable[0]
                # Need to check two-letter vars against list of two letter reseved words
                elif not variable[0:2] in self.reservedVars and not variable[0:2] in self.twoLetterReservedWords:
                    varname = variable[0:2]
                # Neither available, pick one from available
                else:
                    # Find an unused variable name
                    while self.int_to_var_name(varcount) in self.reservedVars or self.int_to_var_name(
                            varcount) in self.twoLetterReservedWords:
                        varcount += 1
                    varname = self.int_to_var_name(varcount)
                # Save var name in the reserved vars
                self.reservedVars[varname] = vartype

                # Add type identifiers if necessary
                for case in switch(vartype):
                    if case('INTDECARRAY'): pass
                    if case('INTDEC'):
                        varname += '%'
                        break
                    if case('STRINGDECARRAY'): pass
                    if case('STRINGDEC'):
                        varname += '$'
                        break

                # Add open array paren if its an array
                if vartype in ("INTDECARRAY", "STRINGDECARRAY", "FLOATDECARRAY"):
                    varname += '('
            # Map old name to new name
            assigned_vars[variable] = varname
            self.decVarList[variable]['asoftvar'] = varname

            # If we are using a predef file, we need to save the definition to it.
            if self.havePreDefs:
                self.predefvars[variable] = self.decVarList[variable]
        self.assignedVars = assigned_vars

    def replace_defined_vars(self):
        """
        Replace the defined variables with the Applesoft variables chosen for them.
        :return:
        """
        new_code = []
        for token in self.tokens:
            if token.tokenID in self.idTokens or token.tokenID in self.arrayRefs:
                # print ("Variable token: " + token[0] + ", " + token[1])
                # See if this variable is in the list to be swapped
                if token.tokenText.upper() in self.assignedVars:
                    # print("Replacing " + token[1].upper() + " with " + self.assignedVars[token[1].upper()])
                    new_code.append(TokenObj(token.filename, token.lineNum,
                                             token.tokenID, self.assignedVars[token.tokenText.upper()]))
                    continue
            # Replacement not necessary, so append token as is.
            new_code.append(token)
        self.tokens = new_code

    def find_next_nonwhitespace_token_type(self):
        """
        Go through the tokens in self.tokens and return the token type of the
        first non-whitespace
        :return: Token type
        """
        count = 0
        if len(self.tokens):
            while self.tokens[count].tokenID == "WHITESPACE":
                count += 1
            return self.tokens[count].tokenID
        else:
            return ""

    @staticmethod
    def find_prev_nonwhitespace_token_type(tokens):
        """
        Finds the type of the last non-whitespace token in list (i.e. from left of list).
        :param tokens: List of tokens
        :return: The type, if any. Empty string if no nonwhitespace tokens found.
        """
        if len(tokens):
            count = len(tokens) - 1
            while tokens[count].tokenID == "WHITESPACE":
                count -= 1
            return tokens[count].tokenID
        else:
            return ""

    def handleLongIfs(self):
        """
        Handle the longif statement, which is in the format:

        longif <expression> then
           code
        [elseif <expression>] then
           code
           . . .
        [else]
           code
        endif

        These ifs can span multiple lines of code, and has elseif & else clauses

        This gets translated to something like this:
         on 2 - ( <expression>) goto @longif-X-start,@longif-X-1
         _longif-X-start
            code
         [goto @longif-X-exit]
         _longif-X-1
         on 2 - (<expression>) goto @longif-X-2-start,@longif-X-2
         _longif-X-2-start
           code
         [goto @longif-X-exit]
         _@longif-X-2 : REM else
           code
         [_longif-X-exit]

         The weird on 2 - <expression> comes from the fact that we want to
         have the result of the boolean expression (0 or 1) jump to one of two
         locations: if it's true, then we want to jump to the label just after the
         if, if it's false. we want it to jump to the first jump label.

         It is possible to nest longifs. The else and endif always apply to
         the innermost longif

         To handle elseif, we have a set of continuations. If the expression isn't
         true, it jumps to the next condition.

         Successful conditions always jump to an exit label.

        :return:
        """
        logger = logging.getLogger('VirtualBasic')

        target_stack = []  # Hold the line labels for the else and endifs.
        continue_stack = []  # Holds counter for elseif targets
        longif_stack = []  # Holds the ID's of longif's we are in currently
        new_code = []  # Transformned code
        if_counter = 0  # Assign numbers to each long if so we can trace them

        while len(self.tokens):
            token = self.tokens.pop(0)
            for case in switch(token.tokenID):
                if case('LONGIF'):
                    # Set up the long if
                    if_counter += 1
                    expr = self.extract_to_token_type(self.tokens, 'THEN')
                    self.tokens.pop(0)  # Get rid of the THEN
                    if expr == 'NONE':
                        # Could not find THEN for this longif
                        logger.error("Error in file {0} line #{1}: Could not find THEN for LONGIF".format(
                            token.filename, token.lineNum))
                        exit(1)
                    startLabel = "longif-{0}-start".format(if_counter)
                    jumpLabel = "longif-{0}-1".format(if_counter)
                    # Begin by pushing the ON. Note the 2- here is to put the true and false
                    # cases in a logical order (true case first, false case second).
                    new_code += self.tokenize_string(token.filename, token.lineNum, "on 2-(")
                    new_code += expr
                    # Complete GOTO portion and add line label
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     ") GOTO @{0},@{1}\n_{0}".format(startLabel, jumpLabel))
                    # Save jumplabel onto the stack
                    longif_stack.append(if_counter)
                    target_stack.append(jumpLabel)
                    continue_stack.append(1)
                    break
                if case('ELSE'):
                    # For else, we need to add a goto to a new label, then add
                    # the previous jump label.

                    # Safety check, ensure we have something on label stack
                    if len(target_stack) < 1:
                        logger.error("Error: filename {0} line #{1}: ELSE without LONGIF.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    continue_count = continue_stack.pop()
                    continue_count += 1
                    if_id = longif_stack[-1]
                    end_label = "longif-{0}-exit".format(if_id)
                    new_code += self.tokenize_string(token.filename, token.lineNum, "\nGOTO @{0}".format(end_label))
                    old_label = target_stack.pop()
                    new_code += self.tokenize_string(token.filename, token.lineNum, "\n_{0}\n".format(old_label))
                    target_stack.append(end_label)
                    continue_stack.append(continue_count)
                    break
                if case('ELSEIF'):
                    # Essentially the same as the IF, but we replace the 
                    # jump target.
                    if len(target_stack) < 1:
                        logger.error("Error filename {0} line #{1}:  ELSEIF without LONGIF.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    continue_count = continue_stack.pop()

                    if_id = longif_stack[-1]
                    end_label = "longif-{0}-exit".format(if_id)
                    new_code += self.tokenize_string(token.filename, token.lineNum, "\nGOTO @{0}\n".format(end_label))
                    old_label = target_stack.pop()
                    new_code += self.tokenize_string(token.filename, token.lineNum, "\n_{0}\n".format(old_label))
                    # need new label
                    continue_count += 1
                    new_label = "longif-{0}-{1}".format(if_counter, continue_count)
                    # Get the elseif expression
                    expr = self.extract_to_token_type(self.tokens, 'THEN')
                    if expr == 'NONE':
                        # Could not find THEN for this longif
                        logger.error("Error in file {0} line #{1}: Could not find THEN for ELSEIF".format(
                            token.filename, token.lineNum))
                        exit(1)

                    self.tokens.pop(0)  # Get rid of then
                    new_code += self.tokenize_string(token.filename, token.lineNum, "on 2-(")
                    new_code += expr
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     ") GOTO @{0},@{1}\n_{0} ".format(new_label + "-start",
                                                                                      new_label))
                    target_stack.append(new_label)
                    continue_stack.append(continue_count)
                    break

                if case('ENDIF'):
                    # Just need to add in the last line label
                    if len(target_stack) < 1:
                        logger.error("Error filename {0} line #{1}: ENDIF without LONGIF.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    # Done with this if, pop it off the stack.
                    ifID = longif_stack.pop()
                    # Get the previous label off of the stack, see if it 
                    # was the end label
                    old_label = target_stack.pop()
                    if old_label[-4:] != "exit":
                        # We didn't have an ELSE clause, so it didn't push an
                        # exit target onto the stack. That means we need to create 
                        # two targets: one for the exit and one for the 
                        # continuation
                        end_label = "longif-{0}-exit".format(ifID)
                        new_code += self.tokenize_string(token.filename, token.lineNum, "\n_{0}\n".format(end_label))
                    new_code += self.tokenize_string(token.filename, token.lineNum, "\n_{0}\n".format(old_label))
                    continue_stack.pop()
                    break
                if case():
                    # Default, just pass token along
                    new_code.append(token)

        self.tokens = new_code

    def handle_asserts(self):
        """
        Handle assert expressions. They are in the format:

        assert <expression>

        If expression is true, nothing happens. If it is false, then the
        program stops with a message that the assertion failed.

        Code translates to this:

        if not(<expression>) then print "Assertion "; <expression> ; " failed.": stop

        :return:
        """
        new_code = []
        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            if token.tokenID == 'ASSERT':
                expr = self.get_remainder_of_statement_or_line(self.tokens)
                # print("Expression is:")
                # self.dump_tokens(expr)
                expr_str = self.de_tokenize(expr)
                failed_message = "Filename {0} Line# {1} :Assertion '{2}' failed".format(
                    token.filename, token.lineNum, expr_str[0].code)
                new_code += self.tokenize_string(token.filename, token.lineNum, "if not (")
                new_code += expr
                new_code += self.tokenize_string(token.filename, token.lineNum,
                                                 ') then print "{0}" : stop\n'.format(failed_message))
            else:
                new_code.append(token)
        self.tokens = new_code

    def replace_question_marks_with_print(self):
        """
        The external Applesoft tokenizer does not convert ? to PRINT for some stupid reason. So, we fix it here.
        """

        # Just iterate over the tokens.
        for token in self.tokens:
            if token.tokenID == 'PRINT':
                # Just set the token text to PRINT to overwrite any "?"
                token.tokenText = 'PRINT'

    def handle_loops(self):
        """
        Handle loop structures

         The while synatax is:
         WHILE <expression> DO
           <code>
         WEND

         This turns into:

         _when-start-X
         IF NOT (<expression>) GOTO @While-X-exit
         <code>
         goto @when-start-X
         _While-X-exit

         And we handle repeat..until:

         REPEAT
           <code>
         UNTIL <expression>

         This translates to:

         _repeat-start-X
           <code>
         IF (<expression>) GOTO @repeat-X-exit
         GOTO @repeat-start-X
         _repeat-X-exit

         We also support:
         break - Jumps out of loop (translates to goto @wend-x | @repeat-exit-X)
         continue - Jumps back to start of loop (translates to goto _when-start-X | _repeat-start-X

         We maintain a stack of loops, so the break and continue correspond to the innermost loop.
         as does the wend/until. This lets you nest loops.
        :return:
        """
        logger = logging.getLogger('VirtualBasic')

        new_code = []
        loop_stack = []  # Track what loops we are currently in
        while_count = 0
        repeat_count = 0

        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            for case in switch(token.tokenID):
                if case('WHILE'):
                    # Handle while by setting up label and if then test
                    while_count += 1
                    while_name = "While-{0}".format(while_count)
                    loop_stack.append(while_name)
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "\n_{0}-start\n".format(while_name))
                    # Start the expression off
                    new_code += self.tokenize_string(token.filename, token.lineNum, "IF NOT (")
                    # Get the expression up to the DO statement

                    new_code += self.extract_to_token_type(self.tokens, "DO")
                    self.tokens.pop(0)  # Get rid of the DO
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     ") THEN GOTO @{0}-exit\n".format(while_name))
                    break
                if case('WEND'):
                    # Pull the top loop off of the loop stack
                    if len(loop_stack) < 1:
                        logger.error(
                            "Error in file {0} line #{1}:  encountered a WEND without a matching WHILE.".format(
                                token.filename, token.lineNum
                            ))
                        exit(1)
                    loop_name = loop_stack.pop()
                    # Ensure this closes a WHILE
                    if loop_name[0:5] != 'While':
                        logger.error("Error in file {0} line #{1}: Attempt to close a REPEAT loop with a WEND".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)

                    # Add in the goto back to the top of the loop, then the label
                    # for the end.
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "\nGOTO @{0}-start\n".format(loop_name))
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "_{0}-exit\n".format(loop_name))
                    break
                if case('REPEAT'):
                    # Set up repeat
                    repeat_count += 1
                    repeat_name = "Repeat-{0}".format(repeat_count)
                    loop_stack.append(repeat_name)
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "\n_{0}-start\n".format(repeat_name))
                    break
                if case('UNTIL'):
                    # Pull the top loop off of the loop stack
                    if len(loop_stack) < 1:
                        logger.error(
                            "Error in file {0} line #{1}: encountered an UNTIL without a matching REPEAT.".format(
                                token.filename, token.lineNum
                            ))
                        exit(1)
                    loop_name = loop_stack.pop()
                    # Ensure this closes a REPEAT
                    if loop_name[0:6] != 'Repeat':
                        logger.error("Error in file {0} line #{1}: Attempt to close a WHILE loop with an UNTIL".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    new_code += self.tokenize_string(token.filename, token.lineNum, "IF (")
                    new_code += self.get_remainder_of_statement_or_line(self.tokens)
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     ") THEN GOTO @{0}-exit\n".format(loop_name))
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "GOTO @{0}-start\n".format(loop_name))
                    new_code += self.tokenize_string(token.filename, token.lineNum, "_{0}-exit\n".format(loop_name))
                    break
                if case('BREAK'):
                    # We jump out of the innermost loop
                    if len(loop_stack) < 1:
                        logger.error("Error in file {0} line #{1}: Attempt to BREAK out of a nonexistant loop.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    loop_name = loop_stack[-1]
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "GOTO @{0}-exit : ".format(loop_name))
                    break
                if case('CONTINUE'):
                    # CONTINUE: jump back to the start of the loop
                    if len(loop_stack) < 1:
                        logger.error("Error in file {0} line #{1}: Attempt to CONTINUE in a nonexistant loop.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    loop_name = loop_stack[-1]
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "GOTO @{0}-start : ".format(loop_name))
                    break
                if case():
                    # Default case... append token
                    new_code.append(token)
        self.tokens = new_code

    def handle_try_catch(self):
        """
        Handle try-catch blocks. This is a wrapper around ONERR, with the added feature that we save off
        old ONERR targets and restore them as necessary.
         TRY-CATCH blocks look like this:

         _readfile
         TRY
             input "File to read:";a$
             print d$;"open ";a$
             input a,b,c
             print d$;"close ";a$
         CATCH ERR_FILE_NOT_FOUND, ERR_FILE_LOCKED
             print "Cannot find file ";a$
             goto @readile
         CATCH ERR_IO_ERROR
             print "Disk I/O Error! Giving up..."
             RETURN
         CATCH ERR_ALL
             print "unexpected error!"
             STOP
         ENDTRY
         // Successful execution falls through to here
         PRINT "Read file!"
         RETURN
        :return:
        """
        logger = logging.getLogger('VirtualBasic')
        new_code = []
        have_trys = False  # Flag whether we have any try blocks. If so, we'll define a few vars
        in_try = False
        first_catch = False
        have_err_all = False
        catch_count = 0
        try_count = 0
        # Loop through all tokens, looking for try-catch related keywords
        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            for case in switch(token.tokenID):
                if case('TRY'):
                    # We have started a try block.
                    if in_try:
                        # Oops. already in a try block. Error out.
                        logger.error("Error in file {0} line #{1}: TRY found within a TRY block.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    in_try = True
                    first_catch = True
                    try_count += 1
                    catch_count = 0
                    have_err_all = False
                    have_trys = True
                    # Add code that saves off the ONERR state
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "vbppTryDepth++ : GOSUB @vbppLibSaveOnerr : ONERR GOTO @vbppTry-{0}-Catch-Start\n".format(
                                                         try_count))
                    # Save state of stack so we can rool back to it in case of error
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "vbppStackPin(vbppTryDepth) = peek(248)")
                    break
                if case('CATCH'):
                    # If this is the first catch, we need to wrap up the TRY portion of the code.
                    # Jump over the catch statements
                    if have_err_all:
                        logger.error(
                            "Error in file {0} line #{1}: ERR_ALL error code must be caught last in a TRY block.".format(
                                token.filename, token.lineNum
                            ))
                        exit(1)

                    catch_count += 1
                    if first_catch:
                        first_catch = False
                        # Call library subroutine to restore previous ONERR handler, if any
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "GOSUB @vbppLibRestoreOnerr : vbppTryDepth-- :")
                        # Jump over CATCH statements
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "GOTO @vbppTry-{0}-End\n".format(try_count))
                        # Insert label that is the target of the ONERR

                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "_vbppTry-{0}-Catch-Start\n".format(try_count))
                        # Disable error handler, clear stack back to the TRY statement,  and Get error value
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         'poke 216,0 : poke 223,vbppStackPin(vbppTryDepth) : CALL -3288 :' \
                                                         ' vbppErrVal = peek(222) : GOSUB @vbppLibRestoreOnerr : vbppTryDepth--\n')
                    else:
                        # Add in jump to end of previous CATCH to go to end of try-catch block
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "GOTO @vbppTry-{0}-End\n".format(try_count))
                        # Add in the label for onerr target
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "_vbppTry-{0}-Catch-{1}\n".format(try_count, catch_count))

                    # Read next token. It should be a numeric constant
                    in_catch_list = 1
                    # flag to indicate whether we're reading a list errors to CATCH
                    first_list_element = True
                    while in_catch_list:
                        self.discard_leading_whitespace(self.tokens)
                        catch_val = self.tokens.pop(0)
                        if catch_val.tokenID != 'INTLITERAL':
                            # Error: can only use int literals (usually from DEFINED values) in a catch list
                            logger.error(
                                "Error in file {0} line #{1}: Non-integer token '{2}' found in catch list.".format(
                                    catch_val.filename, catch_val.lineNum, catch_val.tokenText
                                ))
                            exit(1)
                        if first_list_element:
                            # Handle special case of ERR_ALL
                            if catch_val.tokenText == '9999':
                                have_err_all = True
                                # Ensure that ERR_ALL is not followed by a comma.
                                if not self.get_nth_right_nonspace_token_obj(self.tokens,
                                                                             1).tokenID in self.statementSeps:
                                    # Error: can only use int literals (usually from DEFINED values) in a catch list
                                    logger.error('Error in file {0} line #{1}: Illegal element "{2}"' \
                                                 ' following a ERR_ALL in CATCH statement. ERR_ALL must be' \
                                                 ' the only element in the CATCH list.'.format(
                                        catch_val.filename, catch_val.lineNum,
                                        self.get_nth_right_nonspace_token_obj(self.tokens, 1).tokenText
                                    ))
                                    exit(1)
                                break

                            # Start IF statement
                            new_code += self.tokenize_string(token.filename, token.lineNum,
                                                             "IF NOT (vbppErrVal = {0}".format(catch_val.tokenText))
                            first_list_element = False
                        else:
                            if have_err_all or catch_val.tokenText == '9999':
                                # ERR_ALL must be in a catch by itself, and it must be last.
                                logger.error('Error in file {0} line #{1}: ERR_ALL must be' \
                                             ' only error code in a CATCH statement.'.format(
                                    catch_val.filename, catch_val.lineNum, catch_val.tokenText
                                ))
                                exit(1)
                            new_code += self.tokenize_string(token.filename, token.lineNum,
                                                             " OR vbppErrVal = {0}".format(catch_val.tokenText))
                        # see if we have a comma next. If so, then the list of errors being caught continues
                        if self.get_nth_right_nonspace_token_obj(self.tokens, 1).tokenText != ",":
                            # End of list. Leave loop
                            in_catch_list = False
                        else:
                            self.extract_to_token_type(self.tokens, "PUNCTUATION")
                            foo = self.tokens.pop(0)
                            # print("Popped token type '{0}' value '{1}'".format(foo.tokenID, foo.tokenText))

                    if have_err_all:
                        # Special "catch all" error code. We do not have an IF conditional on it.
                        break
                    # Close off the IF statement
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     ") THEN GOTO @vbppTry-{0}-Catch-{1}\n".format(
                                                         try_count, catch_count + 1))
                    break
                if case('ENDTRY'):
                    # Check for error conditions (not in a TRY, did not have at least one CATCH)
                    if not in_try:
                        logger.error("Error in file {0} line #{1}: ENDTRY found without a TRY block.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    if first_catch:
                        logger.error("Error in file {0} line #{1}: ENDTRY found without any CATCH block.".format(
                            token.filename, token.lineNum
                        ))
                        exit(1)
                    # Close off the previous catch statement with a GOTO
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "GOTO @vbppTry-{0}-End\n".format(try_count))
                    # Insert the last catch label for execution fall through. This label is reached if no CATCH
                    # statement grabbed it.
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "_vbppTry-{0}-Catch-{1}\n".format(try_count, catch_count + 1))
                    # Insert a RESUME. This tells Applesoft to re-run the statement that caused the error. Essentially,
                    # this rethrows the exeception so another TRY block might be able to handle it.
                    new_code += self.tokenize_string(token.filename, token.lineNum, "RESUME\n")
                    # Now add the last label to exit out of the try-catch block.

                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "_vbppTry-{0}-End\n".format(try_count))

                    in_try = False

                    break
                if case():
                    # Default case... append token
                    new_code.append(token)
        if have_trys:
            new_code = self.prepend_try_vars(new_code[0]) + new_code
            new_code += self.append_try_lib_routines(new_code[0])
        self.tokens = new_code

    def prepend_try_vars(self, token):
        try_vars = self.tokenize_string(token.filename, token.lineNum,
                                        "float vbppErrVal : float vbppTryDepth = 0\n")
        # See if we have a definition for MAXTRYDEPTH
        if 'MAXTRYDEPTH' in self.defines:
            max_try_depth = self.defines['MAXTRYDEPTH']
        else:
            max_try_depth = 5
        try_vars += self.tokenize_string(token.filename, token.lineNum,
                                         'float vbppStackPin({0}), vbppCurlSv({0}),' \
                                         ' vbppTextPsv({0}), vbppErrFlag({0})'.format(max_try_depth))

        return try_vars

    def append_try_lib_routines(self, token):
        """
            Generate support code for try/catch to end of source
        :param token: A token to use to get a linenumber and filename to associate with the try/catch code
        """
        tryLib = self.tokenize_string(token.filename, token.lineNum,
                                      "_vbppLibSaveOnerr\n")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "vbppCurlSv(vbppTryDepth) = PEEK(246) + PEEK(247) * 256 :")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "vbppTextPsv(vbppTryDepth) = PEEK(244) + PEEK(245) * 256 :")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "vbppErrFlag(vbppTryDepth) = PEEK(216) : RETURN\n")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "_vbppLibRestoreOnerr\n")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "poke 246, vbppCurlSv(vbppTryDepth)-INT(vbppCurlSv(vbppTryDepth)/256)*256 :")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "poke 247, INT(vbppCurlSv(vbppTryDepth)/256) :")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "poke 244, vbppTextPsv(vbppTryDepth)-INT(vbppTextPsv(vbppTryDepth)/256)*256 :")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "poke 245, INT(vbppTextPsv(vbppTryDepth)/256) :")
        tryLib += self.tokenize_string(token.filename, token.lineNum,
                                       "POKE 216, vbppErrFlag(vbppTryDepth) : RETURN\n")
        return tryLib

    def handle_switch_statements(self):
        """
        Handle Switch statements.
        :return: Nothing
        """

        # Switch statements look like this:
        #
        # Switch (swexp)
        # case (caseexp1)
        #   case1_statements
        # case (caseexp2)
        #   case2_statements
        # . . .
        # default // Optional catchall
        #   default_statement
        # endswitch
        #
        # By default, at the end of a matching case statement, you fall
        # to the endswitch. If no cases match, execution falls through to
        # endswitch
        #
        # Code output for this would be:
        #
        # if not (swexp = caseexp1) goto @vbppswitch_1_case_2
        # case1_statements
        # goto vbppswitch_1_end
        # _vbppswitch_1_case_2
        # if not (swexp = caseexp2) goto @vbppswitch_1_case_3
        # case2_statements
        # goto vbppswitch_1_end
        # . . .
        # _vbppswitch1_caseX
        # default_statements
        # _vbppswitch_1_end
        #
        # Problem that's hard to avoid: if there's no default, you end up with two
        # labels being generated (for the next case, and for the end of the Switch.
        # Avoiding that would require pre-parsing the Switch statement to see if it had
        # a default and how many cases it contains.
        logger = logging.getLogger('VirtualBasic.handle_switch_statements')
        switch_stack = []  # Hold the line labels for the else and endifs.
        switch_expression = []  # Holds the expression we are switching on
        case_stack = []  # Holds counter for elseif targets
        new_code = []  # Transformned code
        switch_counter = 0  # Assign numbers to each long if so we can trace them
        in_switch = False  # Flag to track if we are in a Switch
        have_default = False  # Flag that we have seen a default case
        # self.dump_tokens(self.tokens)

        while len(self.tokens):
            token = self.tokens.pop(0)
            for case in switch(token.tokenID):
                if case('SWITCH'):
                    in_switch = True
                    have_default = False
                    switch_counter += 1
                    switch_exp = self.get_remainder_of_statement_or_line(self.tokens)
                    if len(switch_exp) == 0:
                        logger.error("Error in file {0} line #{1}: SWITCH without argument".format(
                            token.filename, token.lineNum))
                        exit(1)
                    # TODO: Sanity check the content of the Switch argument to ensure it only has variable refs?
                    # Naw... not now.
                    switch_expression.append(switch_exp)  # save expression
                    switch_stack.append(switch_counter)  # save the Switch number we're on
                    case_stack.append(0)  # Stack holding the counter of cases
                    break
                if case('CASE'):
                    if not in_switch:
                        logger.error("Error in file {0} line #{1}: CASE statement outside of a SWITCH".format(
                            token.filename, token.lineNum))
                        exit(1)
                    if have_default:
                        # Uh uh! No cases after we have a default case!
                        logger.error("Error in file {0} line #{1}: CASE statement following a DEFAULT case".format(
                            token.filename, token.lineNum))
                        exit(1)
                    case_exp = self.get_remainder_of_statement_or_line(self.tokens)
                    if len(case_exp) < 1:
                        logger.error("Error in file {0} line #{1}: CASE statement must have an expression".format(
                            token.filename, token.lineNum))
                        exit(1)
                    # Get case number off of stack, add one, and then push it back on
                    case_num = case_stack.pop() + 1
                    case_stack.append(case_num)
                    switch_num = switch_stack[-1]
                    if case_num > 1:
                        # End previous case by going to the end of the Switch
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "\nGOTO @vbpp_Switch_{0}_End\n".format(
                                                             switch_num))
                        # Need to insert landing label from previous case
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "\n_vbpp_Switch_{0}_Case_{1}\n".format(
                                                             switch_num, case_num))
                    # We use negate so execution falls through if case matches, we branch otherwise.
                    new_code += self.tokenize_string(token.filename, token.lineNum, "IF NOT (")
                    new_code += switch_expression[-1]  # Add Switch expression
                    new_code += self.tokenize_string(token.filename, token.lineNum, " = ")
                    new_code += case_exp
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     ') THEN GOTO @vbpp_Switch_{0}_Case_{1}\n'.format(
                                                         switch_num, case_num + 1))
                    break
                if case('DEFAULT'):
                    # Defaults are just like CASEs, excapt we do not have a conditional gateway
                    have_default = True
                    case_num = case_stack[-1]  # Not bothering to increment CASE counter
                    switch_num = switch_stack[-1]
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "\nGOTO @vbpp_Switch_{0}_End\n".format(
                                                         switch_num))
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "\n_vbpp_Switch_{0}_Case_{1}\n".format(
                                                         switch_num, case_num + 1))
                    break
                if case('ENDSWITCH'):
                    if not in_switch:
                        logger.error("Error in file {0} line #{1}: ENDSWITCH without a SWITCH".format(
                            token.filename, token.lineNum))
                        exit(1)
                    if case_stack[-1] == 0:
                        # Didn't have a CASE
                        logger.error("Error in file {0} line #{1}: SWITCH ... ENDSWITCH without a CASE".format(
                            token.filename, token.lineNum))
                        exit(1)
                    switch_num = switch_stack[-1]
                    # If we didn't have a default case, we need to add case label that's the target of the last goto
                    if not have_default:
                        case_num = case_stack[-1]
                        new_code += self.tokenize_string(token.filename, token.lineNum,
                                                         "\n_vbpp_Switch_{0}_Case_{1}\n".format(
                                                             switch_num, case_num + 1))
                    # Insert end label
                    new_code += self.tokenize_string(token.filename, token.lineNum,
                                                     "\n_vbpp_Switch_{0}_End\n".format(
                                                         switch_num))
                    # Pop off stack
                    case_stack.pop()
                    switch_stack.pop()
                    switch_expression.pop()
                    if len(switch_stack) < 1:
                        in_switch = False
                    break
                if case():
                    # Default case... append token
                    new_code.append(token)
        self.tokens = new_code

    def remove_empty_lines_and_statements(self):
        """
        Remove any empty lines or statements from source code. Called when statements might have been deleted from source.
        """
        new_code = []
        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            # Handle redundant statement separator.
            if token.tokenID == "STATEMENTSEP":
                # If next token is Statement seporator EOL, skip
                if self.find_next_nonwhitespace_token_type() in ("STATEMENTSEP", "EOL"):
                    continue
                # Check to see if pervious accepted token was EOL. if so, skip
                elif self.find_prev_nonwhitespace_token_type(new_code) == "EOL":
                    continue
                else:
                    # Separator is legit. Append it to new version of code
                    new_code.append(token)
            elif token.tokenID == "EOL":
                # Skip if next token also a linefeed
                if self.find_next_nonwhitespace_token_type() == "EOL":
                    continue
                else:
                    new_code.append(token)
            else:
                # Not of interest. Append it.
                new_code.append(token)
        self.tokens = new_code

    def replace_hex_constants(self):
        """ Scan the list of tokens and find any literal values that are hex references. If so,
        Convert them to decimal equivalents.
        :return: Nothing
        """
        new_code = []
        while len(self.tokens) > 0:
            token = self.tokens.pop(0)
            if token.tokenID == "HEXCONSTANT":
                value = token.tokenText
                value = value[1:]
                intval = int(value, 16)
                new_code += self.tokenize_string(token.filename, token.lineNum, str(intval))
            else:
                new_code.append(token)
        self.tokens = new_code

    def read_var_file(self):
        """
        Read a .json file that contains predefined mappings of VirtialBasic++ variables to
         Applesoft variables.
        :return: Dictionary containing the predefined variable names and applesoft definitions. If no file was found, returns an empty dict.
        """
        logger = logging.getLogger('VirtualBasic')
        pre_def_vars = {}  # Return empty dict if the file isn't found.
        var_file_name = self.defines["VARFILE"]
        # If file exists, read it. Otherwise, we just return an empty dict.
        if os.path.isfile(var_file_name):
            try:
                with open(var_file_name) as in_file:
                    pre_def_vars = json.load(in_file)
            except:
                e = sys.exc_info()[0]
                logger.error("Error reading variable file {0}: {1}".format(var_file_name, e))
                exit(1)
        logger.info('Read variable file {0}'.format(var_file_name))
        return pre_def_vars

    def write_var_file(self, preDefVars):
        """
        Write the variable definitions out to a file
        :return: None
        """
        logger = logging.getLogger('VirtualBasic.write_var_file')
        varfilename = self.defines["VARFILE"]
        try:
            with open(varfilename, 'w') as out_file:
                json.dump(preDefVars, out_file, sort_keys=True,
                          indent=4, separators=(',', ': '))
        except:
            e = sys.exc_info()[0]
            logger.error("Error writing variable file {0}: {1}".format(varfilename, e))
            exit(1)
        logger.info("Wrote variable file {0}.".format(varfilename))


class Basic(VirtualBasicCode):
    r"""Convert Virtual Basic in ApplesoftBasic
    ex:
    code = Basic(lines,arguments,scriptName)
    code.root = "/home/loz/bas"
    print code.basic()
    print code.msg"""

    def __init__(self, li=[], args=[], naScript="none"):
        VirtualBasicCode.__init__(self, li, args, naScript)

    def basic(self):
        """convert into applesoft basic"""
        logger = logging.getLogger("VirtualBasic.convert")
        result = ""
        self.convert()
        # self.msg += "Converted"
        logger.info("Conversion complete")
        result += "".join(self.lines)
        self.code = result
        return result


# class Fusion(VirtualBasicCode):
#     r"""merge all inserts files in Virtual Basic
#     ex:
#     root = "/home/loz/bas"
#     code = Fusion(lines,root)
#     print code.fusion()
#     print code.msg"""
#
#     def __init__(self, li=[], myRoot=""):
#         VirtualBasicCode.__init__(self, li)
#         self.root = myRoot
#
#     # def insert_files(self):
#     #     """Insert external files into the source. Dead code? Uses the old style inserts."""
#     #     self.otherInsert = 0
#     #
#     #     result = []
#     #     insert_file = re.compile("===insert ([a-zA-Z0-9\/\-\_]+\.baz)===")
#     #     line_with_hash = re.compile("^\s*\#")
#     #     insert_file_with_hash = re.compile("\#[\t\s]*===insert [a-zA-Z0-9\/\-\_]+\.baz===.*")
#     #
#     #     for line in self.lines:
#     #         if insert_file.search(line) and not insert_file_with_hash.search(line):
#     #             m = insert_file.search(line)
#     #             fichier = self.root + "/" + m.group(1)
#     #             try:
#     #                 f = open(fichier, "r")
#     #                 fic = f.readlines()
#     #                 for linefic in fic:
#     #                     if not line_with_hash.search(linefic):
#     #                         linefic = linefic.replace("\n", "")
#     #                         result.append(linefic)
#     #                 f.close()
#     #             except:
#     #                 self.msg += "! Warning can't insert file  " + fichier + " ! \n"
#     #                 # sys.exit(0)
#     #         else:
#     #             line = line.replace("\n", "")
#     #             result.append(line)
#     #
#     #     insert_file = re.compile("===insert [a-zA-Z0-9\/\-\_]+\.baz===")
#     #     for line in result:
#     #         if insert_file.search(line) and not insert_file_with_hash.search(line):
#     #             self.otherInsert = 1
#     #             break
#     #
#     #     self.lines = result
#
#     def fusion(self):
#         """merge all insert files in one file"""
#         result = ""
#         if self.mode == "local" and self.root != "":  # if root not defined don't try to import insert
#             self.insert_files()
#             while self.otherInsert == 1:  # scan again lines to find a new insert
#                 self.insert_files()
#         self.msg += "Merged"
#         result += "\n".join(self.lines)
#         self.code = result
#         return result


class Compression(VirtualBasicCode):
    r"""Compress ApplesoftBasic
    ex:
    code = Compression(lines)
    print code.compression()
    print code.msg"""

    def __init__(self, li=[]):
        VirtualBasicCode.__init__(self, li)

    def compression(self):
        logger = logging.getLogger('VirtualBasic.Compression')
        "compress code"
        result = ""
        self.replace_prints()
        self.delete_rem_lines()
        self.delete_spaces()
        logger.info("Compression complete")
        # self.msg += "Compressed"
        result += "".join(self.lines)
        self.code = result
        return result


class BasToBaz:
    r"""class basic to virtual basic version 0.0.6
    ex: code = BasToBaz(lines)
        text = code.to_virtual()"""

    def __init__(self, li=[]):
        self.lines = li
        self.root = ""
        self.links = {}
        self.linkCount = 0
        self.lastRemName = ""
        self.mode = "local"
        # self.msg = "\n"
        self.ismes = ["absolutism", "absurdism", "academicism", "accidentalism", "acosmism", "adamitism", "adevism",
                      "adiaphorism", "adoptionism", "aestheticism", "agapism", "agathism", "agnosticism", "anarchism",
                      "animism", "annihilationism", "anthropomorphism", "anthropotheism",
                      "antidisestablishmentarianism", "antilapsarianism", "antinomianism", "antipedobaptism",
                      "apocalypticism", "asceticism", "aspheterism", "atheism", "atomism", "autosoterism", "autotheism",
                      "bitheism", "bonism", "bullionism", "capitalism", "casualism", "catabaptism", "catastrophism",
                      "collectivism", "collegialism", "conceptualism", "conservatism", "constructivism", "cosmism",
                      "cosmotheism", "deism", "determinism", "diphysitism", "ditheism", "ditheletism", "dualism",
                      "egalitarianism", "egoism", "egotheism", "eidolism", "emotivism", "empiricism", "entryism",
                      "epiphenomenalism", "eternalism", "eudaemonism", "euhemerism", "existentialism",
                      "experientialism", "fallibilism", "fatalism", "fideism", "finalism", "fortuitism",
                      "functionalism", "geocentrism", "gnosticism", "gradualism", "gymnobiblism", "hedonism", "henism",
                      "henotheism", "historicism", "holism", "holobaptism", "humanism", "humanitarianism", "hylicism",
                      "hylomorphism", "hylopathism", "hylotheism", "hylozoism", "idealism", "identism", "ignorantism",
                      "illuminism", "illusionism", "imagism", "immanentism", "immaterialism", "immoralism",
                      "indifferentism", "individualism", "instrumentalism", "intellectualism", "interactionism",
                      "introspectionism", "intuitionism", "irreligionism", "kathenotheism", "kenotism", "laicism",
                      "latitudinarianism", "laxism", "legalism", "liberalism", "libertarianism", "malism",
                      "materialism", "mechanism", "meliorism", "mentalism", "messianism", "millenarianism", "modalism",
                      "monadism", "monergism", "monism", "monophysitism", "monopsychism", "monotheism", "monotheletism",
                      "mortalism", "mutualism", "nativism", "naturalism", "necessarianism", "neonomianism",
                      "neovitalism", "nihilism", "nominalism", "nomism", "noumenalism", "nullibilism", "numenism",
                      "objectivism", "omnism", "optimism", "organicism", "paedobaptism", "panaesthetism", "pancosmism",
                      "panegoism", "panentheism", "panpsychism", "pansexualism", "panspermatism", "pantheism",
                      "panzoism", "parallelism", "pejorism", "perfectibilism", "perfectionism", "personalism",
                      "pessimism", "phenomenalism", "physicalism", "physitheism", "pluralism", "polytheism",
                      "positivism", "pragmatism", "predestinarianism", "prescriptivism", "primitivism", "privatism",
                      "probabiliorism", "probabilism", "psilanthropism", "psychism", "psychomorphism",
                      "psychopannychism", "psychotheism", "pyrrhonism", "quietism", "racism", "rationalism", "realism",
                      "reductionism", "regalism", "representationalism", "republicanism", "resistentialism",
                      "romanticism", "sacerdotalism", "sacramentarianism", "scientism", "self-determinism",
                      "sensationalism", "siderism", "skepticism", "socialism", "solarism", "solifidianism", "solipsism",
                      "somatism", "spatialism", "spiritualism", "stercoranism", "stoicism", "subjectivism",
                      "substantialism", "syndicalism", "synergism", "terminism", "thanatism", "theism", "theocentrism",
                      "theopantism", "theopsychism", "thnetopsychism", "titanism", "tolerationism", "totemism",
                      "transcendentalism", "transmigrationism", "trialism", "tritheism", "triumphalism", "tuism",
                      "tutiorism", "tychism", "ubiquitarianism", "undulationism", "universalism", "utilitarianism",
                      "vitalism", "voluntarism", "zoism", "zoomorphism", "zootheism"]

    def int2words(self, number):
        """Convert a string of digits to spelled-out digits. For some reason."""
        nums = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
                "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}
        x = str(number)
        s = ""
        for e in x:
            s += nums[e]
        return s[0].lower() + s[1:]

    def isme_name(self, number):
        isme_val = self.ismes.pop()
        return isme_val

    # The original code for converting line number to labels was buggy. It would
    # do a blind find/replace on all numbers, so that if any literal values
    # matched a line number being replace, it too would be replaced. We do it
    # smarter, by only replacing the numbers following a GOTO, GOSUB, or THEN
    def replace_branches(self, lines):
        """Replace goto/gosub/then line number branches"""
        branch_re = re.compile(r'(goto|gosub|then)\s+([0-9]+)')
        new_code = []
        for line in lines:
            if branch_re.search(line):
                line = branch_re.sub(self.branch_rep, line)
            new_code.append(line)
        return new_code

    def branch_rep(self, match):
        """Called by sub to replace the line number with a label. Creates new labels
            as necessary."""
        if match.group(2) in self.links:
            return "{0} @{1}".format(match.group(1), self.links[match.group(2)])
        else:
            self.linkCount += 1
            label = "Label-{0}-".format(self.linkCount)
            self.links[match.group(2)] = label
            return "{0} @{1}".format(match.group(1), label)

    def replace_on_branches(self, lines):
        """ Similar to above, but handles "on (goto|gosub) 10, 20, 30, ..." """
        on_branch_re = re.compile(r"(on\s+.+?(?:goto|gosub)\s+)([0-9\,\s]+)")
        new_code = []
        for line in lines:
            if on_branch_re.search(line):
                line = on_branch_re.sub(self.onBranchRep, line)
            new_code.append(line)
        return new_code

    def on_branch_rep(self, match):
        """Called by the re.sub to replace line numbers with labels. Creates new
            label if necessary"""
        rep = []
        dests = [x.strip() for x in match.group(2).split(',')]

        for dest in dests:
            if dest in self.links:
                rep.append("@" + self.links[dest])
            else:
                self.linkCount += 1
                label = "Label-{0}-".format(self.linkCount)
                self.links[match.group(2)] = label
                rep.append("@" + label)
        return match.group(1) + ", ".join(rep)

    # def find_links(self, lines):
    #     """Another function to find gotos/gosubs/then brahnces, apparently... not sure if this
    #        is live code or not -gg
    #        :param lines: List of strings to operate on
    #        """
    #     result = []
    #     goto_re = re.compile("goto([ 0-9]+)")
    #     gosub_re = re.compile("gosub([ 0-9]+)")
    #     then_re = re.compile("then([ 0-9]+)")
    #     for line in lines:
    #         if goto_re.search(line):
    #             occurrences = goto_re.findall(line)
    #             for res in occurrences:
    #                 if res.strip() not in result:
    #                     result.append(res.strip())
    #         if gosub_re.search(line):
    #             occurrences = gosub_re.findall(line)
    #             for res in occurrences:
    #                 if res.strip() not in result:
    #                     result.append(res.strip())
    #         if then_re.search(line):
    #             occurrences = then_re.findall(line)
    #             for res in occurrences:
    #                 if res.strip() not in result:
    #                     result.append(res.strip())
    #     return filter(None, result)

    def lower_text(self, lines):
        """Lowercase all text in list of strings.
        :param lines: List of strings to operate on
        """
        result = []
        s = ""
        for line in lines:
            s = line.lower()
            result.append(s)
        return result

    def clean_lines(self, lines):
        """Strip line endings from strings in list
        :param lines: List of strings to operate on
        """
        result = []
        crln = re.compile("[\r\n]")
        for line in lines:
            s = crln.sub("", line)
            result.append(s)
        return result

    def delete_first_space(self, lines):
        """Delete leading spaces from list of strings.
        :param lines: List of strings to operate on
        """
        result = []
        space = re.compile("^ +")
        for line in lines:
            s = space.sub("", line)
            result.append(s)
        return result

    def create_links_map(self):
        """Create list of branches in source code"""
        result = {}
        liste = self.findLinks(self.lines)
        liste_int = map(int, liste)
        liste_int.sort()
        for e in liste_int:
            result[str(e)] = self.isme_name(e)
            # result[str(e)] = self.int2words(e)
        return result

    #
    def insert_line_labels(self, lines):
        """Refactoring place_links to be less messy
        :param lines: List of strings to operate on
        """
        results = []
        numbered_re = re.compile("^([0-9]+\s+)(.*)$")
        # byName = re.compile("^([0-9 ]+)rem ->([a-z]+)")
        for line in lines:
            match = numbered_re.match(line)
            if match:
                # See if this is a line that needs a label
                line_num = match.group(1).strip()
                if line_num in self.links:
                    label_line = "\n_{0}".format(self.links[line_num])
                    results.append(label_line)
                results.append(match.group(2))
            else:
                results.append(line)
        return results

    # def place_links(self, lines):
    #     """Handle links in a VirtualBasic-generted AppleSoft program being converted back to
    #        VirtualBasic.
    #        :param lines: List of strings to operate on
    #        """
    #
    #     result = []
    #     number_first = re.compile("^([0-9]+)")
    #     # special for converted virtual basic scripts
    #     by_name = re.compile("^([0-9 ]+)rem ->([a-z]+)")
    #     rem_name = re.compile("rem->([a-z]+)")
    #     for line in lines:
    #         if number_first.search(line):  # numbered lines
    #             m = number_first.search(line)
    #             if rem_name.search(line):  # if rem->link
    #                 m3 = rem_name.search(line)
    #                 self.lastRemName = m3.group(1)
    #
    #             if self.links.has_key(m.group(1)):  # if key in links list
    #                 if by_name.search(line):
    #                     m2 = by_name.search(line)
    #                     s = "_" + m2.group(2)
    #                     self.links[m.group(1)] = m2.group(2)
    #                     self.lastRemName = ""
    #                 elif self.lastRemName != "":
    #                     s = number_first.sub("", line)
    #                     s = "_" + self.lastRemName + "\n" + s.strip()
    #                     self.links[m.group(1)] = self.lastRemName
    #                     self.lastRemName = ""
    #                     del result[-1]  # remove last element of result because is lastRemName
    #                 else:
    #                     s = number_first.sub("", line)
    #                     s = "_" + self.links[m.group(1)] + "\n" + s.strip()
    #                     self.lastRemName = ""
    #             else:  # not in links list
    #                 s = line
    #         else:  # not numbered lines
    #             s = line
    #         result.append(s)
    #     return result

    def place_calls(self, lines):
        """Replace gosub, goto, and then calls with the VirtualBasic @ equivalents
        :param lines: List of strings to operate on
        """
        result = []
        goto_re = re.compile("goto([ 0-9]+)")
        gosub_re = re.compile("gosub([ 0-9]+)")
        then_re = re.compile("then([ 0-9]+)")
        for line in lines:
            if goto_re.search(line):
                occurrences = goto_re.findall(line)
                for res in occurrences:
                    x = res.strip()
                    if x != "":
                        line = line.replace("goto" + res, "goto @" + self.links[x])
            if gosub_re.search(line):
                occurrences = gosub_re.findall(line)
                for res in occurrences:
                    x = res.strip()
                    if x != "":
                        line = line.replace("gosub" + res, "gosub @" + self.links[x])
            if then_re.search(line):
                occurrences = then_re.findall(line)
                for res in occurrences:
                    x = res.strip()
                    if x != "":
                        line = line.replace("then" + res, "goto @" + self.links[x])
            result.append(line)
        return result

    def place_calls_on(self, lines):
        """Replace on x, y, z with equivalaent Virtual Basic calls.
        :param lines: List of strings to operate on
        """
        result = []
        on_re = re.compile(",([ 0-9]+)")
        for line in lines:
            if on_re.search(line):
                occurrences = on_re.findall(line)
                for res in occurrences:
                    x = res.strip()
                    if x != "" and self.links.has_key(x):
                        line = line.replace(res, "@" + self.links[x])
            result.append(line)
        return result

    def delLinesNumbers(self, lines):
        """Delete line numbers.
        :param lines: List of strings to operate on
        """
        result = []
        line_number = re.compile("^([ 0-9]+)")
        for line in lines:
            s = line_number.sub("", line)
            result.append(s)
        return result

    def to_virtual(self):
        """Convert Applesoft to VirtuaLBasic"""
        self.lines = self.cleanLines(self.lines)
        self.lines = self.deleteFirstSpace(self.lines)
        self.lines = self.lowerText(self.lines)
        self.lines = self.replaceOnBranches(self.lines)
        self.lines = self.replace_branches(self.lines)
        self.lines = self.insertLineLabels(self.lines)
        # self.links = self.create_links_map()
        # self.lines = self.place_links(self.lines)
        # self.lines = self.place_calls(self.lines)
        # self.lines = self.place_calls_on(self.lines)
        self.lines = self.delLinesNumbers(self.lines)
        return '\n'.join(self.lines)


if __name__ == "__main__":
    print
    r"""
classes: Basic(), Fusion(), Compression()
attributes:
 lines => list of virtual basic lines
 arguments => 'c' compress, 'u' ultra compress,
 'remgo' show subscript name, 'loz' my copyleft,
 scriptName => if you choose an other script name
 root => root of the project
usage:
 code = Basic(lines,arguments,scriptName)
 code.root = "/root/folder/"
 code.basic() => method return applesoft basic

 code = Fusion(lines,root)
 code.fusion() => method merge all virtual basic scripts in one virtual basic script

 code = Compression(lines)
 code.compression() => method return more compressed applesoft basic code

classe: BasToBaz()
attributes
 lines => list of applesoft basic lines
usage:
 code = BasToBaz(lines)
 code.to_virtual() => return applesoft basic converted in virtual basic

version:
 Virtual Basic tool version 0.2.8
 Copyright � 2011, andres lozano aka loz
 Copyleft: This work is free, you can redistribute it and / or modify it
 under the terms of the Free Art License. You can find a copy of this license
 on the site Copyleft Attitude well as http://artlibre.org/licence/lal/en on other sites.
"""
