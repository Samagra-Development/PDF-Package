"""
Generate Pdf for all the request
"""
import json
import uuid
import os.path
import threading
from time import sleep
from queuelib import FifoDiskQueue
from interface import Interface
from db.app import DB, get_db
from db.models import PdfData, OutputTable, TempData
from utils.func import initialize_logger
from sqlalchemy import desc

class PDFPlugin(Interface):

    ''' **FetchData.process() -> Dict  => Fetches "new" data from the database/server/websocket
     whatever and provides it in the form of dictionary, one PDF at a time.
     **FetchMapping.process() -> Dict => Feches mapping and yeilds it in the form of dictionary
     **BuildPDF.process() -> File => Function to build PDF and return a file
     **UploadPDF.process(key, File) ->  => Fuction to save PDF
     **RetrievePDF.process(key) -> File => Function to get the previously saved PDF from the key'''

    def fetch_data(self):
        """
        Fetches "new" data from the database/server/websocket
        whatever and provides it in the form of dictionary, one PDF at a time
        """

    def fetch_mapping(self, data):
        """
        Feches mapping and yeilds it in the form of dictionary
        """

    def build_pdf(self, raw_data, file_name):
        """
        Function to build PDF and return a file
        """

    def upload_pdf(self, key, file_url):
        """
        Fuction to save PDF
        """

    def retrieve_pdf(self, key):
        """
        Function to get the previously saved PDF from the key
        """

    def delete_file_drive_google_script(self, file):
        """
        Function to delete doc from drive
        :param file:
        :return:
        """

        
class Config:
    """
    define configuration for pdf generation
    """
    @classmethod
    def get_default_config(cls):
        """
        return default configuration
        """
        config = {"retries": 1, "max_concurrency": 2}
        return config

    def __init__(self, config=None):

        self.retries = config["retries"]
        self.max_concurrency = config["max_concurrency"]


class PDFBuilder:
    '''
    initialize itself with any plugin and call its function for pdf generation
    '''
    def __init__(self, plugin, config):
        try:
            PDFPlugin.verify(type(plugin))
            logging = initialize_logger()
            # Get the logger specified in the file
            self.logger = logging.getLogger(__name__)
            self._plugin = plugin
            self._config = Config(config=config)
            self._app = get_db()

        except:
            self.logger.error("Exception occurred", exc_info=True)
            raise ValueError('Please provide a valid plugin. Needs to be an instance of PDFPlugin.')

    def _insert_output_table(self, rec_unique_id, rec_instance_id, rec_doc_url,
                             rec_raw_data, rec_tags, rec_doc_name, rec_pdf_version, rec_url_expires, rec_link_id):
        error = None
        try:
            get_db()
            data_for_output_table = OutputTable(
                unique_id=rec_unique_id,
                instance_id=rec_instance_id,
                doc_url=rec_doc_url,
                raw_data=rec_raw_data,
                tags=rec_tags,
                doc_name=rec_doc_name,
                pdf_version=rec_pdf_version,
                url_expires = rec_url_expires,
                link_id = rec_link_id
                )
            DB.session.add(data_for_output_table)  # Adds new request record to database
            DB.session.commit()  # Commits all changesgetConnection
            #DB.session.flush()
        except Exception as ex:
            error = 'Values not inserted in output table'
            self.logger.error("Exception occurred", exc_info=True)

        return error

    def _process_queue(self, pdf_data):
        """
        function for generating pdf
        """
        error = None
        try:
            with self._app.app_context():
                tries = pdf_data.tries
                tries += 1  # Incrementing the tries
                pdf_data.tries = tries
                mapping_data = self._plugin.fetch_mapping(pdf_data.raw_data)
                mapping_error = mapping_data[1]

                if not mapping_error:
                    pdf_data.raw_data = mapping_data[0]
                    pdf_data.step = 1
                    file_build = self._plugin.build_pdf(pdf_data.raw_data, pdf_data.instance_id)
                    file_name = file_build[0]
                    file_error = file_build[1]
                    if not file_error:
                        pdf_data.step = 2
                        pdf_data.doc_name = file_build[0]
                        pdf_data.doc_url = file_build[2]
                        file_downloaded = self._plugin.upload_pdf(file_name, pdf_data.doc_url)
                        upload_file_url = file_downloaded[0]
                        file_error = file_downloaded[1]
                        if not file_error:
                            pdf_data.step = 3
                            version = pdf_data.pdf_version
                            version += 1
                            pdf_data.pdf_version = version
                            pdf_data.current_status = 'complete'
                            pdf_data.task_completed = True
                            pdf_data.doc_name = upload_file_url
                            pdf_data.url_expires = file_downloaded[2]
                            # Now moving the above data to the Output table
                            inserted_to_output = self._insert_output_table(
                                pdf_data.unique_id, pdf_data.instance_id, pdf_data.doc_url,
                                pdf_data.raw_data, pdf_data.tags,
                                pdf_data.doc_name, pdf_data.pdf_version, pdf_data.url_expires, pdf_data.link_id)

                            if not inserted_to_output:
                                pdf_data.error_encountered = ''
                            else:
                                pdf_data.error_encountered = inserted_to_output
                                pdf_data.task_completed = False
                        else:
                            pdf_data.error_encountered = file_error
                    else:
                        pdf_data.error_encountered = file_error
                else:
                    pdf_data.error_encountered = mapping_error
        except Exception as ex:
            error = "Unable to process queue"
            self.logger.error("Exception occurred", exc_info=True)
        return error, pdf_data

    def start_queue(self):
        """
        function for getting all data from pdfdata table which are not completed yet
        """
        while 1:
            results = []
            qms = PdfData.query.filter(PdfData.tries < self._config.retries,
                                       PdfData.task_completed == False).order_by(desc(PdfData.unique_id)).limit(
                                           self._config.max_concurrency).all()
            if not qms:
                print("Sleeping for 10 seconds")
                sleep(10)  # If no data is found in database sleep for 10 seconds
                #break
            else:
                try:
                    i = 0
                    for data in qms:
                        resp = self._process_queue(data)
                        results.append(resp[1])
                        i += 1
                    DB.session.bulk_save_objects(results)
                    DB.session.commit()
                    #break

                except Exception as ex:
                    self.logger.error("Exception occurred", exc_info=True)

    def _save_pdf_data(self, final_data, tags, linked_instance_id):
        unique_ids = []
        json_data = PdfData(
            raw_data=final_data,
            tags=tags,
            instance_id=uuid.uuid4(),
            link_id = linked_instance_id)
        DB.session.add(json_data)  # Adds new User record to database
        DB.session.flush() # Pushing the object to the database so that it gets assigned a unique id
        unique_ids.append(json_data.unique_id)
        DB.session.commit()  # Commits all changes
        status = 'submitted'
        return {"status": status, "uniqueId": unique_ids}

    def run(self):
        """
        function for calling queue method which generate pdf
        """
        print("Starting program")
        print("-" * 79)
        with self._app.app_context():
            self.start_queue()
        print("Program done")
        print()

    def data_download(self):
        """
        function for saving data from queue into PdfData table
        """
        print("Starting data download")
        print("-" * 79)
        with self._app.app_context():
            while 1:
                da_queue = FifoDiskQueue(os.path.dirname(__file__)+'/../queuedata')
                data = da_queue.pop()
                da_queue.close()
                if not data:
                    print('sleep for 10')
                    sleep(10)
                    #break
                else:
                    raw_data = json.loads(data.decode('utf-8'))
                    self._save_pdf_data(raw_data['reqd_data'], raw_data['tags'],raw_data['instance_id'])
                    break

    def update_tag_pdfdata(self):
        
        while(1):
            qms = TempData.query.filter(TempData.is_update == False).limit(10).all()
            if not qms:
                print("Sleeping for 10 seconds")
                sleep(10)  # If no data is found in database sleep for 10 seconds
                break
            else:
                try:
                    i = 0
                    results = []
                    temp_results = []
                    for data in qms:
                        print(data)    
                        pdf_record = PdfData.query.filter(PdfData.link_id == data.instance_id).all()
                        for rec in pdf_record:
                            if rec.is_update:
                                data.is_update = True
                                temp_results.append(data)
                            else :    
                                results = []
                                raw_data = rec.raw_data
                                req_data = raw_data['req_data']
                                req_data['user_name'] = data.user_name
                                raw_data['USERNAME'] = data.user_name
                                tags = rec.tags
                                tags['USERNAME'] = data.user_name
                                rec.raw_data = raw_data
                                rec.tags = tags
                                rec.is_update = True
                                results.append(rec)
                    i += 1
                    DB.session.bulk_save_objects(results)
                    DB.session.commit()
                    DB.session.bulk_save_objects(temp_results)
                    DB.session.commit()
                    #break
                except Exception as ex:
                    self.logger.error("Exception occurred", exc_info=True)

    def update_tag_outputtable(self):
        
        while(1):
            qms = PdfData.query.filter(PdfData.is_update == True).limit(10).all()
            if not qms:
                print("Sleeping for 10 seconds")
                sleep(10)  # If no data is found in database sleep for 10 seconds
                break
            else:
                try:
                    i = 0
                    results = []
                    for data in qms:
                        print(data)    
                        out_record = OutputTable.query.filter(OutputTable.instance_id == data.instance_id).all()
                        for rec in out_record:
                            out_record.tags = data.tags
                            out_record.raw_data = data.out_record
                            results.append(out_record)
                            i += 1
                    DB.session.bulk_save_objects(results)
                    DB.session.commit()
                    #break
                except Exception as ex:
                    self.logger.error("Exception occurred", exc_info=True)

    def start(self):
        """ function for calling data download
        in one thread and run method in another thread """
        dow_thread = threading.Thread(target=self.data_download)
        run_thread = threading.Thread(target=self.run)
        dow_thread.start()
        run_thread.start()
        dow_thread.join()
        run_thread.join()
        
        
