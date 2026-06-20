import os
import mimetypes
from django.http import FileResponse, Http404
from django.conf import settings


def serve_spa(request, path=''):
    document_root = settings.FRONTEND_BUILD_DIR
    if not path:
        path = 'index.html'

    file_path = os.path.normpath(os.path.join(str(document_root), path))

    if not file_path.startswith(str(document_root)):
        raise Http404()

    if os.path.isfile(file_path):
        content_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(open(file_path, 'rb'))
        if content_type:
            response['Content-Type'] = content_type
        return response

    index_path = os.path.join(str(document_root), 'index.html')
    if not os.path.isfile(index_path):
        raise Http404()

    response = FileResponse(open(index_path, 'rb'))
    response['Content-Type'] = 'text/html'
    return response