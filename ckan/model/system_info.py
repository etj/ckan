# encoding: utf-8

'''
The system_info table and SystemInfo mapped class store runtime-editable
configuration options.

For more details, check :doc:`maintaining/configuration`.
'''

from sqlalchemy import types, Column, Table
from six import text_type

from ckan.model import meta
from ckan.model import core
from ckan.model import domain_object

__all__ = ['system_info_table', 'SystemInfo',
           'get_system_info', 'set_system_info']

system_info_table = Table(
    'system_info', meta.metadata,
    Column('id', types.Integer(),  primary_key=True, nullable=False),
    Column('key', types.Unicode(100), unique=True, nullable=False),
    Column('value', types.UnicodeText),
    Column('state', types.UnicodeText, default=core.State.ACTIVE),
)


class SystemInfo(core.StatefulObjectMixin,
                 domain_object.DomainObject):

    def __init__(self, key, value):

        super(SystemInfo, self).__init__()

        self.key = key
        self.value = text_type(value)


meta.mapper(SystemInfo, system_info_table)


def get_system_info_wrapped(key, default=None):
    ''' get data from system_info table '''
    from sqlalchemy.exc import ProgrammingError
    try:
        obj = meta.Session.query(SystemInfo).filter_by(key=key).first()
        meta.Session.commit()
        if obj:
            return obj.value
    except ProgrammingError:
        meta.Session.rollback()
    return default


def get_system_info(key, default=None):
    ''' get data from system_info table '''
    ''' Tries and fix a sqlalchemy error:
        sqlalchemy.exc.StatementError: (sqlalchemy.exc.InvalidRequestError)
        Can't reconnect until invalid transaction is rolled back'''
    from sqlalchemy.exc import StatementError, InvalidRequestError
    import logging
    try:
        return get_system_info_wrapped(key, default)
    except StatementError as e:
        logging.exception('Error retrieving system info')
        if isinstance(e.orig, InvalidRequestError):
            meta.Session.rollback()
            # try it a second time
            logging.info('Retrying...')
            return get_system_info_wrapped(key, default)


def delete_system_info(key, default=None):
    ''' delete data from system_info table '''
    obj = meta.Session.query(SystemInfo).filter_by(key=key).first()
    if obj:
        meta.Session.delete(obj)
        meta.Session.commit()


def set_system_info(key, value):
    ''' save data in the system_info table '''
    obj = None
    obj = meta.Session.query(SystemInfo).filter_by(key=key).first()
    if obj and obj.value == text_type(value):
        return
    if not obj:
        obj = SystemInfo(key, value)
    else:
        obj.value = text_type(value)

    meta.Session.add(obj)
    meta.Session.commit()
    return True
