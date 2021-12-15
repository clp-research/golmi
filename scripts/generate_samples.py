from app.dynamatt import dynatasks
import sys

import click

print(sys.path)


@click.command()
@click.option('--number_of_samples', type=int, default=10)
@click.option('--dry_run', is_flag=True, type=bool, default=False)
@click.option("-o", '--output_path', type=str, default=None)
def generate_samples_cli(number_of_samples, output_path, dry_run):
    generate_samples(number_of_samples, output_path, dry_run)


def generate_samples(number_of_samples=10, output_path=None, store_strategy=None, dry_run=False):
    """Storage Strategies

        - memory: create only in memory (all tasks must fit in memory)
        - single: create a single file for all tasks (all tasks must fit in memory)
        - multi: create a separate file for each task (only a single task must fit in memory)

        Creates a folder 'generated' at the output_path
    """
    saver = dynatasks.TaskInMemorySaver()
    if output_path is not None:
        saver = dynatasks.TaskSingleFileStorageSaver(output_path)
        if store_strategy == "multi":
            saver = dynatasks.TaskMultiFileStorageSaver(output_path)
    callbacks = [saver]
    if dry_run:
        number_of_samples = 1
    dynatasks.TaskGenerator.create().generate_epoch(number_of_samples, callbacks)


if __name__ == "__main__":
    generate_samples()
