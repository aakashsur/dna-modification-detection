# Instructions
All default values should work.
## l_tarentolae processing
* run data/create_tsv.py to concat all the genome information into a single .tsv file (l_tarentolae.tsv)
* run data/generate_sequences.py to create two files: one containing the center-of-sequence information (centers.csv) and another containing the actual sequence information for each column (sequences.npy)
    - Creates sequences centered around ipd values that are greater than a specified ipd ratio on both strands.
## plasmid processing
* run data/create_tsv_plasmid.py to concat all the plasmid data into a single .tsv file (plasmid.tsv)
* run data/fix_js.py to process the ground truth J information and combine it with plasmid.tsv to create a file containing both information (with consistent namimg) (written to plasmid_and_j.csv)
* run data/generate_sequences_plasmid.py to create four files: two containing the center-of-sequence information for both the bottom (plasmid_bottom_centers.csv) and the top (plasmid_top_centers.csv), and two containing the actual sequence for each column corresponding to those centers (plasmid_bottom_sequences.npy and plasmid_top_sequences.npy respectively)
    - Creates sequences for the entire plasmid

## classification

## TODO roadmap
- [x] update data/create_tsv.py
- [x] update data/create_tsv_plasmid.py
- [x] update data/generate_sequences.py
- [x] update data/generate_sequences_plasmid.py
- [x] update data/fix_js.py
- [ ] update classification code to use new repo format