###############################################################################
# Licensed Material - Property of IBM
# 5724-I63, 5724-H88, (C) Copyright IBM Corp. 2014 - All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure
# restricted by GSA ADP Schedule Contract with IBM Corp.
#
# DISCLAIMER:
# The following source code is sample code created by IBM Corporation.
# This sample code is provided to you solely for the purpose of assisting you
# in the  use of  the product. The code is provided 'AS IS', without warranty or
# condition of any kind. IBM shall not be liable for any damages arising out of 
# your use of the sample code, even if IBM has been advised of the possibility 
# of such damages.
###############################################################################
"""
Created on May 19, 2014

@author: pvs

JSON with "extensions" that turn out to be convenient when using JSON for defining configuration
structure.  The extensions added are:
   1. True and False are valid Boolean values in addition to true and false.
   2. Comments delimited by # character.  Everything after first # character in a line
      is ignored.
   3. NIY - Comments delimited by <!-- this is a comment -->.

For JSON definition see http://www.json.org/
For documentation on JSON transformation to Jython/Python see: http://docs.python.org/2/library/json.html

April 4, 2014: SY: (shiliy@ca.ibm.com) 
  Added code to check trailing commas after an object or an array.  This corrected a defect where a trailing
  comma on { ... }, or [ ... ], would be accepted as correct syntax. 
  
19 May 2014: PVS (pvs@us.ibm.com)
  Started with the original JSON and added extensions as enumerated above.

21 SEP 2015: PVS (pvs@us.ibm.com)
  Made a correction to _getToken() that was subtracting 1 from the current parsing position (pos)
  for the tokenStart.  Subtracting 1 was incorrect particularly when the current parsing position
  is at the start of the line when pos is 0.
  
15 OCT 2016 PVS (pvs@us.ibm.com)
  Corrected a defect in the _getStringToken() method where the backslash character was being retained in the 
  value of the token but it should instead be discarded and the next character consumed from the input stream.

01 MAR 2017 PVS (pvs@us.ibm.com)
  Moved this JSONExtended module to use with the Yet Another Python Library (yapl).
"""

from yapl.utilities.Trace import Trace,Level
from yapl.exceptions.Exceptions import JSONException

TR = Trace(__name__)

SpecialCharacters = ['{', '}', ',', ':', '[', ']']
BooleanTokens = ['true', 'True', 'false', 'False']
NumberTokens = ['int', 'long', 'float']
HexadecimalDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F']
PrimitiveValueTypes = ['string', 'int', 'long', 'float', 'true', 'false', 'null']


class Token:
  """
    Token supports a JSON token.
    
    The following are the token types:
      left brace    - '{'
      right brace   - '}'
      comma         - ','
      colon         - ':'
      left bracket  - '['
      right bracket - ']'
      string
      int, long, float,
      true, false, null
  """
  
  def __init__(self,tokenType,value=None):
    self.tokenType = tokenType
    if (tokenType in SpecialCharacters):
      self.value = tokenType
    elif (tokenType == 'true'):
      self.value = (1 == 1)
    elif (tokenType == 'false'):
      self.value = (1 != 1)
    else:
      self.value = value
    #endIf
  #endDef
  
  def getType(self):
    return self.tokenType
  #endDef
  
  def getValue(self):
    return self.value
  #endDef
#endClass


class JSONDocument:
  """
    JSONDocument supports the transformation of JSON formatted files into the corresponding Jython 
    data structures.  See the load() method.
    
    A JSON "object" is represented as a dictionary.  A JSON "array" is represented
    using a list.  JSON "true" is converted to True and JSON "false" is converted to False.  JSON "null" is 
    converted to None.
    
    JSONDocument also supports the transformation of a given Jython dictionary or list object to the 
    corresponding JSON text output.  The top level object can be a dictionary or a list and the top level
    object may be composed of any recursive combination of dictionaries, lists and "primitive" Jython 
    types, i.e., strings, numbers, True, False, None.  See the dump() method. 
  """
  
  # Indent is used for the dumping of objects to a file.
  Indent = "  "
  
  def __init__(self,inputFile=None,outputFile=None):
    """
      JSON constructor
    """
    self.linenum = 0
    self.prevLine = ""
    self.line = ""
    self.pos = 0
    self.tokenStart = 0
    if (inputFile):
      self.inputFile = inputFile
      self.input = open(inputFile,'r')
    else:
      self.inputFile = None
      self.input = None
    #endIf
    
    if (outputFile):
      self.outputFile = outputFile
      self.output = open(outputFile,'w')
    else:
      self.outputFile = None
      self.output = None
    #endIf
  #endDef
  
  def _flushLine(self):
    """
      Method used to "flush" the current input line to force the parser to move 
      to the next line.  The _flushLine)() method is useful for dealing with 
      comments that are marked using the # character.  
    """
    self.pos = len(self.line)
  #endDef
  
  
  def _getLine(self):
    """
      Return the next line from the input file that has text in it other
      than white space characters.
      Keep track of the line number.
      
      Each input line is stripped of white space from the beginning and end.
      If a line ends up being empty after the stripping operation, then another
      line is processed.   
    """
    self.prevLine = self.line
    # Stripping white space now, is convenient and eliminates white space concerns
    # in downstream methods.
    line = ""
    while (not line):
      line = self.input.readline()
      if (not line):
        # empty line signals EOF 
        break
      else:
        line = line.strip()
        self.linenum += 1
      #endIf
      # If line is empty after the strip()
      # then another line will be read.
    #endWhile
    
    return line
  #endDef
  
    
  def _ungetch(self):
    """
      Move the "cursor" back one character.  The cursor is self.pos in the line.
    """
    if (self.pos > 0):
      self.pos -= 1
    #endIf
  #endDef
  
  
  def _getch(self):
    """
      Return the next character in the input stream.
    """
    if (not self.line or self.pos >= len(self.line)):
      if (not self.input):
        raise JSONException("An input source file has not been provided.")
      #endIf
      self.line = self._getLine()
      self.pos = 0
    #endIf
    
    if (not self.line):
      ch = ""
    else:
      ch = self.line[self.pos]
      self.pos += 1
    #ndiIf
    return ch
  #endDef
  
  
  def _parsingErrorMsg(self,message):
    """
      Add the standard parsing error information to the given message to form a standardized error message.
    """
    return "Parsing line: %d -> %s <- %s" % (self.linenum, self.line, message)
  #endDef
    
  def _parsingDiagnostic(self,message):
    """
      Emit a message to stdout that provides diagnostic information for a parsing error.
    """
    if (self.prevLine): print "%s" % self.prevLine
    print "%s" % self.line
    print "%s^-- %s" % (self.tokenStart * ' ', message)
  #endDef
    
  def _getStringToken(self):
    """
      Return a string token instance from the input.
      
      At the point where getStringToken() is invoked, the leading double quote has already been consumed.
      
      15 OCT 2016 (PVS) This method is just wrong in the way it deals with escaped characters.  I need to 
      fix this.  See the JSON spec.  The following are escaped characters:
         \"  is replaced with "
         \\ is replaced with \
         \/ is replaced with /
         \b is replaced with the backspace character
         \f is replaced with the form feed character
         \n is replaced with the new line character
         \r is replaced with the carriage return character
         \t is replaced wit the tab character
         \u#### is replaced with the given hexadecimal unicode character
    """
    value = ""
    done = 0
    while not done:
      ch = self._getch()
      if (ch == '"'):
        token = Token('string',value)
        break
      elif (ch == '\\'):
        # The \ is discarded and the next character is appended to value
        ch = self._getch()
        value += ch
        if (ch == 'u'):
          # get 4 hexadecimal digits
          i = 0
          while i < 4:
            ch = self._getch()
            if ch not in HexadecimalDigits:
              raise JSONException("In line: %s, expected a hexadecimal digit  but got: '%s', when parsing a string token." % (self.line, ch))
            else:
              value += ch
            #endIf
            i += 1
          #endWhile
        #endIf
      else:
        value += ch
      #endIf
    #endWhile
    return token
  #endDef
  
  
  def _getNumberToken(self,ch):
    """
      Return a number token instance from the input.
      
      The given character is a minus sign (dash) or a digit character.
    """
    tokenType = 'integer'
    number = ch    
    ch = self._getch()
    while (ch.isdigit()):
      number += ch
      ch = self._getch()
    #endWhile

    if (ch == '.'):
      tokenType = 'float'
      number += ch
      ch = self._getch()
      while (ch.isdigit()):
        number += ch
        ch = self._getch()
      #endWhile
    #endIf
    
    if (ch in ['e', 'E']):
      tokenType = 'float'
      number += ch
      ch = self._getch()
      if (ch in ['+','-']):
        number += ch
        ch = self._getch()
      #endIf
      while (ch.isdigit()):
        number += ch
        ch = self._getch()
      #endWhile
    #endIf
    
    # push back whatever character marked the end of the number
    self._ungetch()
    
    # Roughly, an int can have 10 digits and a total length of 11
    # if there is a leading minus sign.  Anything longer than that
    # that is not a float is treated as a long.  To be really 
    # precise we'd have to check the number string more carefully.
    
    if (tokenType == 'integer'):
      # could be int or long
      if (number[0] == '-' and len(number) > 11):
        tokenType = 'long'
        value = long(number)
      elif (number[0].isdigit() and len(number) > 10):
        tokenType = 'long'
        value = long(number)
      else:
        tokenType = 'int'
        value = int(number)
      #endIf
      token = Token(tokenType,value)
    elif (tokenType == 'float'):
      value = float(number)
      token = Token('float',value)
    #endIf
    
    return token
  #endDef
  
  
  def _getBooleanToken(self,ch):
    """
      Return a boolean token instance from the input.
      
      The given character is a t|T or an f|F.
    """
    if (ch == 't'):
      expecting = "true"
      tokenType = "true"
    elif (ch == 'T'):
      expecting = "True"
      tokenType = "true"
    elif (ch == 'f'):
      expecting = "false"
      tokenType = "false"
    elif (ch == 'F'):
      expecting = "False"
      tokenType = "false"
    else:
      self._parsingDiagnostic("Expecting the starting character of a Boolean token to be either t|T or f|F.")
      raise JSONException("Parsing line: %d -> %s <- Column: %d. Expecting the starting character of a Boolean token to be either t|T or f|F." % (self.linenum,self.line.strip(),self.pos))
    #endIf
    
    tokenLength = len(expecting)
    for i in range(tokenLength):
      c = expecting[i]
      if (ch != c):
        msg = "Expected: '%s'  but got: '%s', when parsing Boolean token." % (c, ch)
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
      #endIf
      # In order to avoid reading past the end of true or false,
      # only read another character when appropriate.
      if (i < tokenLength-1):
        ch = self._getch()
      #endIf
    #endFor
    token = Token(tokenType)
    return token
  #endDef
  
  
  def _getNullToken(self,ch):
    """
      Return the null token from the input.
      
      The given ch must be 'n' and the next three characters must be 'ull'
    """
    expecting = "null"
    tokenLength = len(expecting)
    for i in range(tokenLength):
      c = expecting[i]
      if (ch != c):
        raise JSONException("Parsing line: %d - %s Column: %d. Expected: '%s' but got: '%s', when parsing null token." % (self.linenum, self.line, self.pos, c, ch))
      #endIf
      if (i < tokenLength-1):
        ch = self._getch()
      #endIf
    #endFor
    token = Token("null")
    return token
  #endDef
  
  def _skipWhiteSpaceAndComment(self):
    """
      Helper for _getToken() that skips over white space and comment text.
      
      Comment text starts with a # character and goes to the end of the line.
      
    """
    done = 0
    while not done:
      ch = self._getch()
      while ch.isspace(): ch = self._getch()
      
      if (ch == '#'):
        self._flushLine()
      else:
        self._ungetch()
        done = 1
      #endIf
    #endWhile
    
  #endDef
  
  
  def _getToken(self):
    """
      Return the next JSON token available from the input stream.
      Special characters: left brace, right brace, left bracket, right bracket, comma, colon
    """
    methodName = "_getToken"
    
    self._skipWhiteSpaceAndComment()
    
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName, "Getting token from line -> %s <- Starting at position: %d" % (self.line,self.pos))
    #endIf
    
    self.tokenStart = self.pos
    ch = self._getch()
    if (ch in SpecialCharacters): 
      token = Token(ch)
    elif (ch == '"'):
      token = self._getStringToken()
    elif (ch.isdigit() or ch == '-'):
      token = self._getNumberToken(ch)
    elif (ch in ['t','T','f','F']):
      token = self._getBooleanToken(ch)
    elif (ch == 'n'):
      token = self._getNullToken(ch)
    else:
      msg = "Unexpected input character: %s in JSON file." % ch
      self._parsingDiagnostic(msg)
      msg = self._parsingErrorMsg(msg)
      raise JSONException(msg)
    #endIf
    
    if (TR.isLoggable(Level.FINEST)):
      TR.finest(methodName,"Token type: %s  Token value: %s" % (token.tokenType,token.value))
    #endIf
    return token   
  #endDef
      

  def _getObject(self):
    """
      Return a Jython dictionary that represents a JSON object.
      
      The opening brace has already been consumed.
    """
    methodName = "_getObject"
    
    result = {}
    token = self._getToken()
    previousToken = token
    while (token.tokenType != '}'):
      if (token.tokenType != 'string'):
        msg = "Parsing a JSON object.  Expected a string that is an attribute name, but got: '%s'" % token.tokenType
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
      #endIf
      key = token.value
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Attribute name: '%s'" % key)
      #endIf
      token = self._getToken()
      if (token.tokenType != ':'):
        msg = "Parsing a JSON object. Expected a colon, but got: '%s'" % token.tokenType
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
      #endIf
      value = self._getValue()
      if (TR.isLoggable(Level.FINEST)):
        TR.finest(methodName,"Attribute value: '%s'" % value)
      #endIf
      result[key] = value
      # get a comma or the closing }
      token = self._getToken()
      previousToken = token
      if (token.tokenType == ','):
        token = self._getToken()  # get the next key, which should be a string
      elif (token.tokenType != '}'):
        msg = "Parsing a JSON object. Expected a comma or closing brace, but got token type: '%s' with value: '%s'" % (token.tokenType,token.value)
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
      #endIf
    #endWhile
    
    if (previousToken.tokenType == ','):
        msg = "Parsing a JSON object. Got an extra comma before the closing brace"
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
    #endIf
    
    return result
  #endDef
  
  
  def _getArray(self):
    """
      Return a Jython list that represents a JSON array.
    """
    result = []
    token = self._getToken()
    while (token.tokenType != ']'):
      if (token.tokenType == '['):
        value = self._getArray()
        result.append(value)
      elif (token.tokenType == '{'):
        value = self._getObject()
        result.append(value)
      elif (token.tokenType in PrimitiveValueTypes):
        value = token.value
        result.append(value)
      else:
        msg = "Parsing an array and expecting a value, but got: '%s'" % token.tokenType
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
      #endIf
      token = self._getToken()
      if (token.tokenType == ','):
        nextToken = self._getToken()
        # Check for spurious trailing comma, i.e., a ,] combination
        if (nextToken.tokenType == ']'):
          msg = "Parsing an array and expecting another array item, but got a closing bracket"
          self._parsingDiagnostic(msg)
          msg = self._parsingErrorMsg(msg)
          raise JSONException(msg)
        else:
          token = nextToken
        #endIf
      elif (token.tokenType != ']'):
        msg = "Parsing an array and expecting a comma or closing bracket, but got: '%s'" % token.tokenType
        self._parsingDiagnostic(msg)
        msg = self._parsingErrorMsg(msg)
        raise JSONException(msg)
      #endIf
    #endWhile
    return result
  #endDef
  
    
  def _getValue(self):
    """
      Return a JSON "value".  A value can be a primitive object such as a string, number, true, false or null.
      A value may also be an object or an array.
    """
    token = self._getToken()
    if (token.tokenType in PrimitiveValueTypes):
      value = token.value
    elif (token.tokenType == '{'):
      value = self._getObject()
    elif (token.tokenType == '['):
      value = self._getArray()
    else:
      msg = "Expecting a primitive value type, an array or object but got: '%s'" % token.tokenType
      self._parsingDiagnostic(msg)
      msg = self._parsingErrorMsg(msg)
      raise JSONException(msg)
    #endIf
    return value 
  #endDef
  
  
  def load(self,inputFile=None):
    """
      Load the content of the input file that is assumed to be well-formed JSON into the corresponding
      Jython data objects.
      
      If inputFile is provided it is a pathname to the JSON file to be loaded and it becomes the
      input file associated with this instance of JSONDocument.
      Otherwise, the input file is assumed to have been provided to the JSONDocument constructor when
      it was instantiated. 
    """
    if (inputFile):
      self.inputFile = inputFile
      self.input = open(inputFile,'r')
    elif (self.inputFile):
      self.input = open(self.inputFile,'r')
    else:
      raise JSONException("No input file defined for this instance of JSONDocument.")
    #endIf
    
    self.linenum = 0
    self.pos = 0 
    token = self._getToken()
    if (token.tokenType == '['):
      result = self._getArray()
    elif (token.tokenType == '{'):
      result = self._getObject()
    else:
      result = token.value
    #endIf
    if (self.input):
      self.input.close()
      self.input = None
    #endIf
    return result
  #endDef
  
  
  def _primitiveType(self,obj):
    """
      Return true if the given object is not a list or dictionary.
      Otherwise return false.
    """
    return not (type(obj) == type([]) or type(obj) == type({}))
  #endDef
  
  
  def _primitiveToString(self,obj):
    """
      Return the JSON representation of the given primitive object.
      Primitive objects are string, number, True, False, None.
    """
    if (not self._primitiveType(obj)):
      raise JSONException("Expecting a primitive type but got %s" % type(obj))
    #endIf
    
    if (type(obj) == type("") or type(obj) == type(u"")):
      s = '"%s"' % obj
    else:
      s = "%s" % obj
    #endIf
    return s
  #endDef
  
  
  def _dumpList(self,obj,indentLevel=0,leftMargin=0,trailingComma=''):
    """
      Dump a list object to the output file at the given indentLevel from the given leftMargin.
    """
    if (type(obj) != type([])):
      raise JSONException("Expected an object of type list but got type: %s" % type(obj))
    #endIf

    indent = ' ' * leftMargin  + JSONDocument.Indent * indentLevel
    self.output.write("%s[\n" % indent)
    indentLevel += 1
    secondIndent = indent + JSONDocument.Indent
    listLen = len(obj)
    comma = ','
    for i in range(listLen):
      if (i == listLen - 1): comma = ''
      value = obj[i]
      if (self._primitiveType(value)):
        valueString = self._primitiveToString(value)
        self.output.write('%s%s%s\n' % (secondIndent,valueString,comma))
      else:
        newLeftMargin = leftMargin + len(JSONDocument.Indent) * indentLevel
        if (type(value) == type([])):
          self._dumpList(value,leftMargin=newLeftMargin,trailingComma=comma)
        elif (type(value) == type({})):
          self._dumpDictionary(value,leftMargin=newLeftMargin,trailingComma=comma)
        else:
          raise JSONException("Expected primitive type, list or dictionary, but got: %s" % type(value))
        #endIf
      #endIf
    #endFor
    self.output.write("%s]%s\n" % (indent,trailingComma))
  #endDef
  
  
  def _dumpDictionary(self,obj,leftMargin=0,indentLevel=0,trailingComma=''):
    """
      Dump a dictionary object to the output file at the given indentLevel from the given leftMargin.
      
      leftMargin is the the "column" where the current left margin starts.  
      indentLevel is the number of indents from the left margin
    """
    if (type(obj) != type({})):
      raise JSONException("Expected an object of type dictionary but got type: %s" % type(obj))
    #endIf
    
    indent = ' ' * leftMargin  + JSONDocument.Indent * indentLevel
    self.output.write("%s{\n" % indent)
    keys = obj.keys()
    numKeys = len(keys)
    indentLevel += 1
    secondIndent = indent + JSONDocument.Indent
    i = 0
    comma = ','
    for i in range(numKeys):
      if (i == numKeys - 1): comma = '' 
      key = keys[i]
      value = obj[key]
      if (self._primitiveType(value)):
        valueString = self._primitiveToString(value)
        self.output.write('%s"%s": %s%s\n' % (secondIndent,key,valueString,comma))
      else:
        self.output.write('%s"%s":\n' % (secondIndent,key))
        keyLength = len(key)
        # The "+ 4" is for the double quotes, : and space when dumping out the key
        newLeftMargin = leftMargin + len(JSONDocument.Indent) * indentLevel + keyLength + 4
        if (type(value) == type([])):
          self._dumpList(value,leftMargin=newLeftMargin,trailingComma=comma)
        elif (type(value) == type({})):
          self._dumpDictionary(value,leftMargin=newLeftMargin,trailingComma=comma)
        else:
          raise JSONException("Expected primitive type, list or dictionary, but got: %s" % type(value))
        #endIf
      #endIf
    #endFor
    self.output.write("%s}%s\n" % (indent,trailingComma))
  #endDef
  
  
  def dump(self,obj,outputFile=None):
    """
      Write the JSON representation of the given object (obj) to a file
      
      obj is expected to be either a list or a dictionary
      
      If the optional outputFile argument is not provided, then it is expected that an output
      file path was defined when the JSONDocument object instance was created.
      
      TODO - At some point consider how to deal with Jython class types.
      Maybe do something like have a "toJSON()" method that emits a JSON representation to the
      given file.
    """
    
    if (outputFile):
      self.outputFile = outputFile
      self.output = open(outputFile,'w')
    elif (self.outputFile):
      self.output = open(self.outputFile,'w')
    else:
      raise JSONException("No output file defined for this instance of JSONDocument.")
    #endIf
    
    if (type(obj) == type([])):
      self._dumpList(obj)
    elif (type(obj) == type({})):
      self._dumpDictionary(obj)
    else:
      raise JSONException("Expected top level object to be a list or dictionary but got %s." % type(obj))
    #endIf
    
    if (self.output):
      self.output.close()
      self.output = None
    #endIf
  #endDef
#endClass

