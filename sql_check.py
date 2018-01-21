#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import argparse
import re


"""
本程序用于检测给定的文件中包含的sql语句是否包含破坏性语句.
检查点包含:
    1. delete from必须包含where限定条件
    2. create table只用于创建tmp开头的表格
    3. drop table只用于tmp开头的表格
    4. truncate table只用于tmp开头的表格
    5. alter table只用于tmp开头的表格
"""


def log_error(msg, line_no, line):
    sys.stderr.write('{msg} at line {line_no}: {line}'.format(msg=msg,line_no=line_no, line=line))
    pass


def extract_table_name(action, tokens):
    # CREATE [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name
    #    (create_definition,...)
    #    [table_options]
    #    [partition_options]
    if action == 'create':
        table_name_token_index = 2
        if tokens[1] == 'temporary':
            table_name_token_index += 1
        if 'exists' in tokens:
            table_name_token_index += 3

    # TRUNCATE [TABLE] tbl_name
    if action == 'truncate':
        table_name_token_index = 2 if tokens[1] == 'table' else 1

    # DROP [TEMPORARY] TABLE [IF EXISTS]
    #     tbl_name [, tbl_name] ...
    #     [RESTRICT | CASCADE]
    if action == 'drop':
        table_name_token_index = 2
        if 'temporary' in tokens:
            table_name_token_index += 1
        if 'exists' in tokens:
            table_name_token_index += 2

    # ALTER TABLE tbl_name
    #     [alter_specification [, alter_specification] ...]
    #     [partition_options]
    if action == 'alter':
        table_name_token_index = 2

    # DELETE [LOW_PRIORITY] [QUICK] [IGNORE]
    #     tbl_name[.*] [, tbl_name[.*]] ...
    #     FROM table_references
    #     [WHERE where_condition]
    #
    # DELETE [LOW_PRIORITY] [QUICK] [IGNORE]
    #     FROM tbl_name[.*] [, tbl_name[.*]] ...
    #     USING table_references
    #     [WHERE where_condition]
    # TODO: 暂时不考虑第一种删除语法以及同时删除多个表格数据的语法
    if action == 'delete':
        table_name_token_index = 2
        if 'low_priority' in tokens:
            table_name_token_index += 1
        if 'quick' in tokens:
            table_name_token_index += 1
        if 'ignore' in tokens:
            table_name_token_index += 1
    return tokens[table_name_token_index]


def check(filename):
    sys.stdout.write('Starting to check sql statements in file {0}\n'.format(filename))
    err_cnt = 0
    line_no = 1
    with open(filename, 'r') as f:
        for line in f:
            if line:
                line = line.lower()
                tokens = re.findall(r"[\w']+", line)
                action = tokens[0] if len(tokens) > 0 else None
                if action in ('create', 'alter', 'drop', 'truncate'):
                    table_name = extract_table_name(action, tokens)
                    if not table_name.startswith('tmp'):
                        log_error('Performing illegal actions on a non-tmp table', line_no, line)
                        err_cnt += 1

                if action == 'delete':
                    if 'where' not in line:
                        log_error('Delete data without where conditions', line_no, line)
                        err_cnt += 1
            line_no += 1
    sys.stdout.write('Finished checking the file. Error line count: {0}\n'.format(err_cnt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check illegal sql statements in a specific file')
    parser.add_argument('file', type=str, help='path to the sql file')
    args = parser.parse_args()
    check(args.file)

