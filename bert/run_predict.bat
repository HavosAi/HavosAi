python D:\Bert_fine_tuning\bert\run_classifier.py ^
  --task_name=MRPC^
  --do_predict=true^
  --data_dir=D:\glue-data\MRPC^
  --vocab_file=D:\uncased_L-12_H-768_A-12\vocab.txt^
  --bert_config_file=D:\uncased_L-12_H-768_A-12\bert_config.json^
  --init_checkpoint=D:\mrpc_output\model.ckpt-343^
  --max_seq_length=128^
  --output_dir=D:\mrpc_output\predict_output