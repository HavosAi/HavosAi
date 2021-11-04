python D:\Bert_fine_tuning\bert\run_classifier.py ^
  --task_name=MRPC^
  --do_train=true^
  --do_eval=true^
  --data_dir=D:\glue-data\MRPC ^
  --vocab_file=D:\uncased_L-12_H-768_A-12\vocab.txt^
  --bert_config_file=D:\uncased_L-12_H-768_A-12\bert_config.json^
  --init_checkpoint=D:\uncased_L-12_H-768_A-12\bert_model.ckpt^
  --max_seq_length=128^
  --train_batch_size=32^
  --learning_rate=2e-5^
  --num_train_epochs=3.0^
  --output_dir=D:\mrpc_output