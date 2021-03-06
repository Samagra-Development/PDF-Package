"""
Define Model Use
"""
import pprint
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .app import DB

def object_as_dict(obj):
    """
    convert object into dict
    """
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


class PdfData(DB.Model):
    """
    Define table which save request received
    """
    __tablename__ = 'queuemanager'
    #__bind_key__ = 'pdfbuilder'
    unique_id = DB.Column(
        DB.Integer, primary_key=True)  # unique_id from the request
    instance_id = DB.Column(
        DB.String(256), default=None)  # Id of the instance if available
    #pdfgenerated = relationship("OutputTable", uselist=False, back_populates="pdfdata")
    link_id = DB.Column(
        DB.String(256), default=None)  # Id of the linked instance if available
    raw_data = DB.Column(
        JSONB)  # All the received content (the request)
    tags = DB.Column(
        JSONB)  # All the mapping content
    doc_url = DB.Column(
        DB.String(256)
    )  # google doc url of the generated document (will get doc id from it)
    current_status = DB.Column(
        DB.String(32),
        default='Queue')  # Queue, Processing, Failed, complete, ERROR
    # 0->data fetch,1->mapping fetch,2->pdf build,3-> upload pdf, 4-> short url,
    # 5->deleted from drive
    step = DB.Column(
        DB.Integer,
        default=0)
    tries = DB.Column(
        DB.Integer, default=0)  # No. of attempts trying to process the request
    url_expires = DB.Column(
        DB.BigInteger, default=0)  # Timestamp when the url generated expires
    doc_name = DB.Column(
        DB.Text
    )  # Url of google doc on aws, google storage
    long_doc_url = DB.Column(
        DB.Text
    )
    pdf_version = DB.Column(
        DB.Integer, default=0)  # The PDF version (max 5 allowed)
    error_encountered = DB.Column(DB.String())  # Google app script url
    task_completed = DB.Column(
        DB.Boolean, default=False)  # Is the process completed True/False
    is_update = DB.Column(
        DB.Boolean, default=False)  # Is the process completed True/False
    is_delete = DB.Column(
        DB.Boolean, default=True)  # Is the doc deleted True/False
    def __repr__(self):
        """
        return table unique id
        """
        return '{}'.format(self.unique_id)

    def dump(self):
        """
        print data in string format
        """
        pr_p = pprint.PrettyPrinter(indent=4)
        pr_di = object_as_dict(self)
        pr_p.pprint(pr_di)


class OutputTable(DB.Model):
    """
    Define output table which save request processed
    """
    __tablename__ = 'outputtable'
    #__bind_key__ = 'pdfbuilder'
    unique_id = DB.Column(
        DB.Integer, primary_key=True)  # unique_id from the request
    pdftable_id = DB.Column(
        DB.Integer, DB.ForeignKey('queuemanager.unique_id'))  # unique_id from the request

    instance_id = DB.Column(
        DB.String(256), default=None)  # Id of the instance if available
    link_id = DB.Column(
        DB.String(256), default=None)  # Id of the linked instance if available
    raw_data = DB.Column(
        JSONB)  # All the received content (the request)
    doc_url = DB.Column(
        DB.String(128)
    )  # google doc url of the generated document (will get doc id from it)
    url_expires = DB.Column(
        DB.BigInteger, default=0)  # Timestamp when the url generated expires
    tags = DB.Column(
        JSONB)  # All the mapping content
    doc_name = DB.Column(DB.Text)  # google doc File name on
    pdf_version = DB.Column(
        DB.Integer, default=1)  # The PDF version (max 5 allowed)
    def __repr__(self):
        """
        return table unique id
        """
        return '{}'.format(self.unique_id)
class TempData(DB.Model):
    """
    Define table which save request received
    """
    __tablename__ = 'temp_req'
    #__bind_key__ = 'pdfbuilder'
    unique_id = DB.Column(
        DB.Integer, primary_key=True)  # unique_id from the request
    instance_id = DB.Column(
        DB.String(256), default=None)  # Id of the instance if available
    form_id = DB.Column(
        DB.String(256), default=None)  # Id of the linked instance if available
    user_name = DB.Column(
        DB.String(256), default=None)  # Id of the linked instance if available
    is_update = DB.Column(
        DB.Boolean, default=False)  # Is the process completed True/False

    def __repr__(self):
        """
        return table unique id
        """
        return '{}'.format(self.unique_id)

    def dump(self):
        """
        print data in string format
        """
        pr_p = pprint.PrettyPrinter(indent=4)
        pr_di = object_as_dict(self)
        pr_p.pprint(pr_di)

class BackupPdfData(DB.Model):
    """
    Define table which save request received
    """
    __tablename__ = 'queuemanagerbackup'
    __bind_key__ = 'backup'
    unique_id = DB.Column(
        DB.Integer, primary_key=True)  # unique_id from the request
    link_id = DB.Column(
        DB.String(256), default=None)  # Id of the linked instance if available

    raw_data = DB.Column(
        JSONB)  # All the received content (the request)
    def __repr__(self):
        """
        return table unique id
        """
        return '{}'.format(self.unique_id)

    def dump(self):
        """
        print data in string format
        """
        pr_p = pprint.PrettyPrinter(indent=4)
        pr_di = object_as_dict(self)
        pr_p.pprint(pr_di)
