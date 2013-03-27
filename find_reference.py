#!/usr/bin/env python

'find_reference.py -- find reference of specific word'

import os
import sys
import getopt
from clang.cindex import *
import find_reference_util as frutil

conf = Config()
refer_curs = []

def usage():
    print "Usage:%s"
    print "-h, --help: print help message"
    print "-v, --version: print version message"
    print "-n : target reference name(spelling)"
    print "-f : target reference file name"
    print "-l : target reference line"
    print "-c : target reference column"
    print "-d : directory to find reference"
    print "-o : output result to a file"

def version():
    print "find reference : 1.0 beta"

def printToCmd(curs):
    for c in curs:
        if isinstance(c, Cursor):
            print "-------------------------------------"
            print "file : %s" % os.path.abspath(c.location.file.name)
            cur_parent = frutil.getCallFunc(c)
            if cur_parent:
                print "Call function:",
                out_str = cur_parent.displayname
                if out_str == None:
                    out_str = cur_parent.spelling

                if cur_parent.lexical_parent and not cur_parent.lexical_parent.kind == CursorKind.TRANSLATION_UNIT:
                    print "%s::%s"%(cur_parent.lexical_parent.displayname, out_str)
                else:
                    print out_str
            elif c.lexical_parent and not c.lexical_parent.kind == CursorKind.TRANSLATION_UNIT:
                print "lexical parent : class %s"%c.lexical_parent.displayname

            print c.location.line, c.location.column

def writeToFile(curs, file_path):
    assert(file_path)
    file = open(file_path, "w")

    for c in curs:
        if isinstance(c, Cursor):
            file.write("-----------------------------------------------\n")
            file.write("file : %s\n" % os.path.abspath(c.location.file.name))
            cur_parent = frutil.getCallFunc(c)
            if cur_parent:
                file.write("Call function : \t")
                out_str = cur_parent.displayname
                if out_str == None:
                    out_str = cur_parent.spelling

                if cur_parent.lexical_parent and not cur_parent.lexical_parent.kind == CursorKind.TRANSLATION_UNIT:
                    file.write("%s::%s\n"%(cur_parent.lexical_parent.displayname, out_str))
                else:
                    file.write(out_str+"\n")
            elif c.lexical_parent:
                 file.write("lexical parent : class %s\n"%c.lexical_parent.displayname)

            file.write("line : %s, column :%s \n"%(c.location.line, c.location.column))


def parseFileCB(file, ref):
    if not os.path.exists(file):
        print "file %s don't exists\n"%file
        return
    tu = TranslationUnit.from_source(file, ["-std=c++11"])
    hasDiagnostics = False
    for dia in tu.diagnostics:
        hasDiagnostics = True
        print dia
    if hasDiagnostics == True:
        print "skip file %s"%file
        return

    cur_cursors = frutil.getCursorsWithParent(tu, ref)
    #don't forget to define global refer_curs'
    refer_curs.extend(cur_cursors)

def getDeclarationCursorUSR(cursor):
    assert(isinstance(cursor, Cursor))
    decCursor = conf.lib.clang_getCursorReferenced(cursor)
    if isinstance(decCursor, Cursor):
        return decCursor.get_usr()
    return None

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
            curs_dic["%s, %s, %s"%(os.path.abspath(cur.location.file.name), cur.location.line, cur.location.column)] = cur

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
        if opt in ("-v", "--version"):
            version()
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
    tuSource = TranslationUnit.from_source(os.path.abspath(sourceFileName), ["-std=c++11"])
    assert(isinstance(tuSource, TranslationUnit))

    hasDiagnostics = False
    for diag in tuSource.diagnostics:
        hasDiagnostics = True
        print diag

    if hasDiagnostics == True:
        os.sys.exit(-1)

    tarCursor = frutil.getCursorForLocation(tuSource, refName, line, column)
    if not tarCursor:
        print "Error : Can't get source cursor, please check file:%s, name:%s, line:%s, column:%s info"%(sourceFileName, refName, line, column)
        sys.exit(-1)
    assert(isinstance(tarCursor, Cursor))

    refUSR = getDeclarationCursorUSR(tarCursor)
    
    frutil.scanDirParseFiles(tarDir, parseFileCB, refName)

    final_output = removeFakeByUSR(refer_curs, refUSR)

    if outputFileName:
        writeToFile(final_output, outputFileName)
    else:
        printToCmd(final_output)

if __name__ == "__main__":
    main()

