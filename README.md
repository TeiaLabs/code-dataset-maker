# code-dataset-maker

Gather repo lists by language from the Github API (`github_dataset_maker.get_repos`) and build scripts to clone, clean, and extract metadata from them (`github_dataset_maker.clone_repos`).

Both modules are executable and provide a helpful CLI.

## usage

```bash
python -m github_dataset_maker.get_repos \
    --lang apex \
    --mode ranged \
    --stars 75 100 \
    --step 0

# ./apex_75-100.csv and ./apex_75-100.txt will be created

python -m github_dataset_maker.clone_repos \
    --custom-ssh-key ~/.ssh/id_ecdsa-john \
    --destination-dir /mnt/storage/apex-oss \
    --languages java \
    --repo-list-path apex_75-100.txt

# ./clone.sh will be created. Run with bash clone.sh
```
