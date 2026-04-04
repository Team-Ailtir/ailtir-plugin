# Usage

## Uploading a tender

### With a file path

If you already know the path to your ZIP file, pass it as an argument:

```
/ailtir:tender-upload /Users/alice/Downloads/tender_docs.zip
```

Claude will confirm the path and run the upload immediately.

### Without a file path

If you omit the path, Claude will use the filesystem browser to help you locate
the ZIP file:

```
/ailtir:tender-upload
```

Claude will browse `~/Downloads` and `~/Documents` and ask you to confirm the file
before uploading.

## What happens during upload

1. The `ailtir` CLI registers the file with the Ailtir API
2. The ZIP is uploaded directly to secure cloud storage
3. On success, Claude reports the **knowledge base ID** (`kb_id`)

Example output:

```
Uploading tender_docs.zip...
Upload complete. kb_id: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
```

## Analysing a tender

Once the upload completes, trigger knowledge base ingestion:

```
/ailtir:analyse aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
```

If you omit the `kb_id`, Claude will run `/ailtir:list` and ask you to pick one.
Ingestion takes a few minutes. Use `/ailtir:list` to check when status changes to
`ready`.

## Listing knowledge bases

```
/ailtir:list
```

Shows all knowledge bases in your account with their name, `kb_id`, and current
status (`pending`, `processing`, `ready`, or `error`).

## Chatting with a knowledge base

Once a knowledge base is `ready`, ask questions against it:

```
/ailtir:chat aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa "What is the submission deadline?"
```

Claude sends the question along with the last five conversation interactions as
context, giving the CLI enough background to produce more accurate answers.

## Typical workflow

```
/ailtir:tender-upload /Users/alice/Downloads/tender_docs.zip
/ailtir:analyse <kb_id>
/ailtir:list
/ailtir:chat <kb_id> "What is the submission deadline?"
```

## Troubleshooting

| Error | Likely cause | Fix |
|---|---|---|
| `Error: file_path must be an absolute path` | A relative path was passed | Use a full path starting with `/` |
| `Error: file not found` | The file does not exist at that path | Check the path and try again |
| `Error registering KB: 401` | Invalid or missing secret key | See [configuration.md][] |
| `ailtir: command not found` | CLI not installed or not on PATH | See [installation.md][] |
| `kb_id not found` | Wrong ID or KB not yet created | Run `/ailtir:list` to verify |

[configuration.md]: ./configuration.md
[installation.md]: ./installation.md
