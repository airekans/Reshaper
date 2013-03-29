#!/usr/bin/env python

'find_reference.py -- find reference of specific word'

import os, sys, getopt
from clang.cindex import TranslationUnit
from clang.cindex import Cursor
from clang.cindex import CursorKind
from reshaper.util import get_tu
import reshaper.find_reference_util as frutil
from functools import partial

refer_curs = []

def usage():
    print "Usage:%s"
    print "-h, --help: print help message"
    print "-n : target reference name(spelling)"
    print "-f : target reference file name"
    print "-l : target reference line"
    print "-c : target reference column"
    print "-d : directory to find reference"
    print "-o : output result to a file"

def printToCmd(tarCursor, curs):
    assert(isinstance(tarCursor, Cursor))

    print 
    print "Reference of \"%s\": file : %s, location %s %s"%\
            (tarCursor.displayname, tarCursor.location.file.name, \
            tarCursor.location.line, tarCursor.location.column)
    for c in curs:
        if not isinstance(c, Cursor):
            continue

        print "-------------------------------------"
        print "file : %s" % os.path.abspath(c.location.file.name)
        if c.kind == CursorKind.CXX_METHOD:
            print "class : %s" % c.semantic_parent.spelling \
                    if c.semantic_parent is not None else None
        elif c.kind == CursorKind.FUNCTION_DECL:
            if c.semantic_parent is not None and c.semantic_parent.kind == CursorKind.NAMESPACE:
                print "namespace : %s" % c.semantic_parent.spelling \
                        if not c.semantic_parent.spelling == ''\
                        else "anonymouse namespace"
            else:
                print "global func"

        else:
            cur_parent = frutil.getCallFunc(c)
            if cur_parent:
                print "Call function:",
                out_str = cur_parent.displayname
                if out_str == None:
                    out_str = cur_parent.spelling
                print out_str

        print c.location.line, c.location.column

def writeToFile(tarCursor, curs, file_path):
    assert(file_path)
    assert(isinstance(tarCursor, Cursor))
    file = open(file_path, "w")

    file.write("\n")
    file.write("Reference of \"%s\": file %s, location %s %s\n"%(\
            tarCursor.displayname, tarCursor.location.file.name, \
            tarCursor.location.line, tarCursor.location.column))
    for c in curs:
        if not isinstance(c, Cursor):
            continue
        file.write("-----------------------------------------------\n")
        file.write("file : %s\n" % os.path.abspath(c.location.file.name))
        if c.kind == CursorKind.CXX_METHOD:
            if c.semantic_parent is not None:
                file.write("class : %s\n" %c.semantic_parent.spelling)
        elif c.kind == CursorKind.FUNCTION_DECL:
            if c.semantic_parent is not None and\
                    c.semantic_parent.kind == CursorKind.NAMESPACE:
                if c.semantic_parent.spelling is None:
                    file.write("Anonymouse namespace")
                else:
                    file.write("namespace : %s\n"%c.semantic_parent.spelling)
        else:
            cur_parent = frutil.getCallFunc(c)
            if cur_parent:
                file.write("Call function : ")
                out_str = cur_parent.displayname
                if out_str == None:
                    out_str = cur_parent.spelling
                file.write("%s\n"%out_str)

        file.write("line : %s, column :%s \n"%(c.location.line, c.location.column))

def getDeclarationCursorUSR(cursor):
    decCur = frutil.getDeclarationCursor(cursor)
    if isinstance(decCur, Cursor):
        return decCur.get_usr()
    return None

def parseFileCB(file, ref):
    if not os.path.exists(file):
        print "file %s don't exists\n"%file
        return
    tu = get_tu(file)
    if frutil.checkDiagnostics(tu.diagnostics):
        print "Warning : diagnostics occurs, skip file %s"%file
        return

    cur_cursors = frutil.getCursorsWithParent(tu, ref)
    #don't forget to define global refer_curs'
    refer_curs.extend(cur_cursors)

'''Convert list of Cursors to dict'''
def removeFakeByUSR(cursors, tarUSR):
    assert(tarUSR)
    curs_dic = {}
    for cur in cursors:
        assert(isinstance(cur, Cursor))
        if cur.kind == CursorKind.CALL_EXPR and len(list(cur.get_children())) > 0:
            continue 
        curUSR = getDeclarationCursorUSR(cur)
        
        #FIXME:template class and template function; its declaration USR is different from USR after template instantiations, such as call, template speciallization 
        if curUSR == tarUSR:
            curs_dic["%s%s%s"%(\
                    os.path.abspath(cur.location.file.name), \
                    cur.location.line, cur.location.column)] = cur
    sorted(curs_dic.items())

    return curs_dic.values()

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvn:f:l:c:n:d:o:")
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(-1)

    sourceFileName = None
    line = None
    column = None
    refName = None
    tarDir = None
    outputFileName = None

#get input args    
    for opt, value in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        if opt in ("-f"):
            sourceFileName = value
        if opt in ("-n"):
            refName =  value
        if opt in ("-l"):
            line = value
        if opt in ("-c"):
            column = value
        if opt in ("-d"):
            tarDir = value
        if opt in ("-o"):
            outputFileName = value

#check input args
    if sourceFileName is None:
        print "please input referce file name"
        usage()
        sys.exit(-1)

    if not os.path.isfile(sourceFileName):
        print "file %s is not exists, please check it!"%sourceFileName
        sys.exit(-1)

    if refName is None:
        print "please input referce name"
        usage()
        sys.exit(-1)

    if line is None:
        print "please input referce line No."
        usage()
        sys.exit(-1)
    line = int(line)

    if column is not None:
        column = int(column)

    if tarDir is None:
        tarDir = os.path.abspath("./")
        print "Warning : forget to input tarDir, will take curent directory : %s as target"%tarDir

    if column is None:
        print "Warning : forget to input column, the first one in %s line %s will be chosen"%(sourceFileName, line)

    if not os.path.exists(tarDir):
        print "directory %s is not exists, please check it!"%tarDir

    if outputFileName:
        if not os.path.isfile(outputFileName):
            tmpOutFile = os.path.abspath("./")+"/referenceResult.txt"
            print "Warning : %s don't exists, will create one under current directory :%s"%(outputFileName, tmpOutFile)
            outputFileName = tmpOutFile
     
#get target reference info
    tuSource = get_tu(os.path.abspath(sourceFileName))
    assert(isinstance(tuSource, TranslationUnit))

    if frutil.checkDiagnostics(tuSource.diagnostics):
        print "Warning : file %s, diagnostics occurs, parse result may be incorrect!"%sourceFileName

    tarCursor = frutil.getCursorForLocation(tuSource, refName, line, column)
    if not tarCursor:
        print "Error : Can't get source cursor, please check file:%s, name:%s, line:%s, column:%s info"%(sourceFileName, refName, line, column)
        sys.exit(-1)
    refUSR = getDeclarationCursorUSR(tarCursor)
    
#parse input directory
    frutil.scanDirParseFiles(tarDir, partial(parseFileCB, ref = refName))
    final_output = removeFakeByUSR(refer_curs, refUSR)

#output result
    if outputFileName:
        writeToFile(tarCursor, final_output, outputFileName)
    else:
        printToCmd(tarCursor, final_output)

if __name__ == "__main__":
    main()

