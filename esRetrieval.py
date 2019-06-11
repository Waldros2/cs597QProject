import datetime
import csv
import sys
from collections import defaultdict
from elasticsearch import Elasticsearch
import yaml

#Establish date range

# Read in the YAML file
YAML_file = open(sys.argv[1])
try:
    config = yaml.safe_load(YAML_file)
except yaml.YAMLError as exc:
    print(exc)

start_seq = config['elastic_search']['start_date'].split('.')
start_date = datetime.datetime(int(start_seq[0]), int(start_seq[1]), int(start_seq[2]))

end_seq = config['elastic_search']['end_date'].split('.')
end_date = datetime.datetime(int(end_seq[0]),int(end_seq[1]),int(end_seq[2]))

date_diff = end_date - start_date

# #Establish ElasticSearch
es = Elasticsearch(hosts=config['elastic_search']['host_list'])

#Establish indices for the days
indices = []
while start_date <= end_date:
    indices.append('logstash-' + start_date.strftime('%Y.%m.%d'))
    start_date += datetime.timedelta(days=1)
print(indices)

#Collect from days
for index in indices:
    print('Collecting ' + config['elastic_search']['search_type'] + ' data from ' + index)
    connect_dict = defaultdict(float)
    try:
        res = es.search(index=index, q=config['elastic_search']['query'], size=10000, scroll='1m')
        while len(res['hits']['hits']) > 0:
            for hit in res['hits']['hits']:
                #Collecting netflow data
                if(config['elastic_search']['search_type'] == 'byte'):
                    netflow = hit['_source']['netflow']
            
                    #Establish src/dst
                    if('192.168' not in netflow['ipv4_src_addr']):
                        src = 'superNode'
                    else:
                        src = netflow['ipv4_src_addr']
                        
                    if('192.168' not in netflow['ipv4_dst_addr']):
                        dst = 'superNode'
                    else:
                        dst = netflow['ipv4_dst_addr']
                
                    connect_dict[(src,dst)] += (netflow['out_bytes'] / 2**20)
                    connect_dict[(dst,src)] += (netflow['in_bytes'] / 2**20)
                elif(config['elastic_search']['search_type'] == 'dns'):
                    src = hit['_source']['src_ip']
                    dst = hit['_source']['dest_ip']
                    connections[(src,dst)] += 1

            scroll = res['_scroll_id']
            res = es.scroll(scroll_id=scroll, scroll='1m')
        with open(config['elastic_search']['save_path'] + config['elastic_search']['search_type']+ '_' + index + '.csv', 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['src', 'dst', 'aggregation'])
            for key, value in connect_dict.items():
                    writer.writerow([key[0], key[1], value])
    except Exception as e:
        print('Could not collect from ' + index)
        print(e)