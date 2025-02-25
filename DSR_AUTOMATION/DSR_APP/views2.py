from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.db import connection
from .forms import FileFieldForm
import traceback
from difflib import SequenceMatcher
import re
from .models import DSR
from django.shortcuts import get_object_or_404
import os
import re
from django.views.decorators.csrf import csrf_exempt
import logging
from DSR_APP.services.sap_query_conn import execute_query, create_connection
from .mapping import chain_mapping, db_mapping
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
from datetime import datetime
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from decimal import Decimal
from django.db import transaction #For batch processing
import uuid  # For generating unique instance identifiers



def validate_dsr(request):
    pass