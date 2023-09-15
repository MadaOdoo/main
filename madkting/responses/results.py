# -*- coding: utf-8 -*-
# File:           results.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-03-20


def get_results_report():
    """
    :return: dictionary with standard results format
    :rtype: dict
    """
    return {
        'success': False,
        'has_errors': False,
        'errors': list(),
        'warnings': list(),
        'data': False
    }


def add_error(code, description=False):
    """
    :param code:
    :type: str
    :param description:
    :type: str
    :return:
    :rtype: dict
    """
    return {'code': code, 'description': description}


def error_result(code=False, description=False):
    """
    :param code:
    :type: str
    :param description:
    :type: str
    :return:
    :rtype: dict
    """
    result = get_results_report()
    result['success'] = False
    if code:
        result['has_errors'] = True
        result['errors'].append(add_error(code, description))
    else:
        result['has_errors'] = False
    return result


def error_results(errors):
    """
    :param errors: list of dict errors [{'code':str, 'description': str},...]
    :type errors: list
    :return:
    """
    result = error_result()
    result['has_errors'] = True
    result['errors'] = errors
    return result


def success_result(data=False, warnings=False):
    """
    :param data:
    :param warnings:
    :return:
    """
    result = get_results_report()
    result['success'] = True
    result['has_errors'] = False
    result['data'] = data
    if warnings:
        if isinstance(warnings, list):
            result['warnings'] = warnings
        else:
            result['warnings'].append(warnings)
    return result
