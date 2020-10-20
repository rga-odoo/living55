# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging, ast, zipfile, json, base64, werkzeug.wrappers
from datetime import datetime
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO

from odoo import http,api
from odoo.http import request
from odoo.addons.web.controllers.main import Binary


class ChannelEnginePublicAccess(Binary):
    
    @http.route(['/image/<string:model>/<int:id>/<string:field>/<string:filename>','/image'], type='http', auth="public")
    def ce_product_image_access(self, model='ir.attachment', id=None, field='datas', filename=None, filename_field='datas_fname',
                     download=None, mimetype=None, width=0, height=0):
        """
            Example: http://erpify:8021/parnells/image/ce.product.images/1/product_image/icon.png
        """
        if model not in ['ce.product.images'] and field == 'image':
            return request.not_found()

        status, headers, content = request.registry['ir.http'].ce_publlic_binary_content(model=model, id=id, field=field,
                                                                                      filename=filename,
                                                                                      filename_field=filename_field,
                                                                                      download=download,
                                                                                      mimetype=mimetype,
                                                                                      default_mimetype='image/png')

        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            return request.not_found()

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response 

    @http.route('/web/binary/ce_download_document', type='http', auth="public")
    def ce_download_document(self, attachment_ids, **kw):
        attachment_ids = ast.literal_eval(attachment_ids)
        attachment_ids = request.env['ir.attachment'].search([('id', 'in', attachment_ids)])
        file_dict = {}
        for attachment_id in attachment_ids:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = attachment_id.name
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = dict(path=file_path, name=file_name)
        zip_filename = datetime.now()
        zip_filename = "CE Packing Slip %s.zip" % zip_filename
        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        for file_info in file_dict.values():
            zip_file.write(file_info["path"], file_info["name"])
        zip_file.close()
        headers = [
            ('Content-Type', 'application/x-zip-compressed'),
            ('Content-Disposition', 'attachment; filename=' + zip_filename + ';')
        ]
        return request.make_response(bitIO.getvalue(),headers)


