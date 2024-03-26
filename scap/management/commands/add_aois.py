import sys
import os
from django.core.management.base import BaseCommand
import scap.api
import datetime


class Command(BaseCommand):
    help = ''

    # Parsing params
    # def add_arguments(self, parser):
    #    parser.add_argument('--etl_dataset_uuid', nargs='?', type=str, default=None)
    #    parser.add_argument('--start_date', nargs='?', type=str, default=None)
    #    parser.add_argument('--end_date', nargs='?', type=str, default=None)

    # Function Handler

    # Function Handler
    def handle(self, *args, **options):
        scap.api.generate_geodjango_objects_aoi()
