# -*- coding: utf-8 -*-
import base64
import hashlib
import mimetypes
import os
import re

from odoo import models, tools
from odoo.exceptions import AccessError
from odoo.http import request, STATIC_CACHE, content_disposition
from odoo.tools import pycompat
from odoo.tools.mimetypes import guess_mimetype
from odoo.modules.module import get_resource_path, get_module_path


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def ce_publlic_binary_content(cls, model='ir.attachment', id=None, field='datas', filename=None,
                               filename_field='datas_fname', download=False, mimetype=None,
                               default_mimetype='application/octet-stream', access_token=None):
        """ Get file, attachment content

        If the ``id`` parameter is omitted, fetches the default value for the
        binary field (via ``default_get``), otherwise fetches the field for
        that precise record.

        :param str model: name of the model to fetch the binary from
        :param int id: id of the record from which to fetch the binary
        :param str field: binary field
        :param str mimetype: mintype of the field (for headers)
        :param str default_mimetype: default mintype if no mintype found
        :returns: (status, headers, content)
        """
        # get object and content
        env = request.env
        obj = None
        if id and model in env.registry:
            obj = env[model].sudo().browse(int(id))

        # obj exists
        if not obj or not obj.exists() or field not in obj:
            return (404, [], None)

        # check read access
        try:
            last_update = obj['__last_update']
        except AccessError:
            return (403, [], None)

        status, headers, content = None, [], None

        # attachment by url check
        module_resource_path = None
        if model == 'ir.attachment' and obj.type == 'url' and obj.url:
            url_match = re.match("^/(\w+)/(.+)$", obj.url)
            if url_match:
                module = url_match.group(1)
                module_path = get_module_path(module)
                module_resource_path = get_resource_path(module, url_match.group(2))
                if module_path and module_resource_path:
                    module_path = os.path.join(os.path.normpath(module_path), '')  # join ensures the path ends with '/'
                    module_resource_path = os.path.normpath(module_resource_path)
                    if module_resource_path.startswith(module_path):
                        with open(module_resource_path, 'rb') as f:
                            content = base64.b64encode(f.read())
                        last_update = pycompat.text_type(os.path.getmtime(module_resource_path))

            if not module_resource_path:
                module_resource_path = obj.url

            if not content:
                status = 301
                content = module_resource_path
        else:
            content = obj[field] or ''

        # filename
        if not filename:
            if filename_field in obj:
                filename = obj[filename_field]
            elif module_resource_path:
                filename = os.path.basename(module_resource_path)
            else:
                filename = "%s-%s-%s" % (obj._name, obj.id, field)

        # mimetype
        mimetype = 'mimetype' in obj and obj.mimetype or False
        if not mimetype:
            if filename:
                mimetype = mimetypes.guess_type(filename)[0]
            if not mimetype and getattr(env[model]._fields[field], 'attachment', False):
                # for binary fields, fetch the ir_attachement for mimetype check
                attach_mimetype = env['ir.attachment'].search_read(
                    domain=[('res_model', '=', model), ('res_id', '=', id), ('res_field', '=', field)],
                    fields=['mimetype'], limit=1)
                mimetype = attach_mimetype and attach_mimetype[0]['mimetype']
            if not mimetype:
                mimetype = guess_mimetype(base64.b64decode(content), default=default_mimetype)

        headers += [('Content-Type', mimetype), ('X-Content-Type-Options', 'nosniff')]

        # cache
        etag = bool(request) and request.httprequest.headers.get('If-None-Match')
        retag = '"%s"' % hashlib.md5(pycompat.to_text(content).encode('utf-8')).hexdigest()
        status = status or (304 if etag == retag else 200)
        headers.append(('ETag', retag))
        headers.append(('Cache-Control', 'max-age=%s' % (STATIC_CACHE)))

        # content-disposition default name
        if download:
            headers.append(('Content-Disposition', cls.content_disposition(filename)))
        return (status, headers, content)