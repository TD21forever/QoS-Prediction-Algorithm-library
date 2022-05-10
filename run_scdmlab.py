import argparse
from scdmlab.quick_start.quick_start import run_scdmlab

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', type=str, default='LDCF', help='name of models')
    parser.add_argument('--dataset', '-d', type=str, default='WSDream-1', help='name of datasets')
    parser.add_argument('--dataset_type', type=str, default='rt', help='dataset type')
    parser.add_argument('--config_files', type=str, default=None, help='config files')
    args, _ = parser.parse_known_args()

    config_file_list = args.config_files.strip().split(' ') if args.config_files else None

    run_scdmlab(model=args.model, dataset=args.dataset, config_file_list=config_file_list)