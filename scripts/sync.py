import argparse
import json
import sys

sys.path.append('../src')
from commons import elastic


def print_model(model):
    objects = model['objects']
    print('{} objects:'.format(len(objects)))
    for obj in objects:
        print('\t{} - {} - {}'.format(obj['type'],
                                      obj['attributes']['title'], obj['id']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()    
    parser.add_argument('action')
    parser.add_argument('dashboard_id')
    parser.add_argument('kibana_host')
    parser.add_argument('elastic_host')
    args = parser.parse_args()

    es = elastic.ElasticClient(args.elastic_host,
                               args.kibana_host, "", "")

    file_name = '{}.json'.format(args.dashboard_id)

    if 'export-dashboard' == args.action:
        model = es.export_dashboard(args.dashboard_id)
        print_model(model)
        with open(file_name, 'w') as f:
            json.dump(model, f, indent=4, sort_keys=True)
        print('saved to {}'.format(file_name))

    if 'import-dashboard' == args.action:
        print('reading from {}'.format(file_name))
        with open(file_name) as f:
            model = json.load(f)
        print_model(model)
        es.import_dashboard(model, args.dashboard_id)
        print('done')
