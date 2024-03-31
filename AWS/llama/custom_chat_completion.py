# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

# Modified version of example_chat_completion.py in https://github.com/facebookresearch/llama
# that allows you to specify a custom user message with the flag --user_message as follows:
#
# torchrun --nproc_per_node 1 custom_chat_completion.py \
#    --ckpt_dir llama-2-7b-chat/ \
#    --tokenizer_path tokenizer.model \
#    --max_seq_len 512 --max_batch_size 6
#    --user_message "Tell me about Conduit, the LLM-based text editor."

def main(
    user_message: str,  # New argument for the user-provided message
        
    ckpt_dir: str,
    tokenizer_path: str,
    temperature: float = 0.6,
    top_p: float = 0.9,
    max_seq_len: int = 512,
    max_batch_size: int = 8,
    max_gen_len: Optional[int] = None,
):
    generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
    )

    dialog = [
        {
            "role": "system",
            "content": """\
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.""",
        },
        {"role": "user", "content": user_message},  # User-provided message
    ]

    results = generator.chat_completion(
        [dialog],  # Pass the dialog list as a list element
        max_gen_len=max_gen_len,
        temperature=temperature,
        top_p=top_p,
    )

    print(f"User: {user_message}\n")
    print(
        f"Assistant: {results[0]['generation']['content']}"  # Access the generated response
    )
    print("\n==================================\n")

if __name__ == "__main__":
    fire.Fire(main)