import activity_streams
import json
from get_offline_settings import *


if __name__ == "__main__":
    pagesize = settings_offline.page_size
    collection_uri = settings_offline.collection
    number_of_members, member_list = activity_streams.get_members(
        activity_streams.get_iiif_collection(collection_uri=collection_uri))
    activity_streams_pages = activity_streams.streamer(number_of_members=number_of_members, member_list=member_list,
                                                       top_uri=collection_uri,
                                                       service_uri=settings_offline.service_base_address,
                                                       size_of_page=number_of_members)
    p = activity_streams.page_slicer(activity_streams_pages=activity_streams_pages, position=0)
    with open(settings_offline.output_file, 'w') as output:
        json.dump(p, output, indent=4)
