# Using it with CoWork

This plugin can also be used with Claude CoWork.

It is designed to work with and complement [Claude for Small Business][csb].

Claude CoWork is only available with/through the Claude Desktop App (on Windows and Mac; not on Linux).

## Developing for CoWork

The plugin will be developed by two developer personas ...

- the skill developer and ...
- the tool developer

The skill developer is a business domain expert that will make changes to all the `SKILLS.md` files to add new features/capabilities and/or improve existing ones.

We expect that occasionally the skill will need a tool (public-domain or ailtir-cli/-mcp) that is not available yet. Then the tool developer (a software engineer) will add that tool to unblock the skill developer.

Both developers will just make the/their changes and then commit and push these changes to the repo.

## Testing the Plugin

For now we do not have automated tests for the plugin.

Testing will happen on two levels. 

The tool developer(s) will install the plugin in claude-code and will make sure that the plugin can be installed and the skills can be loaded. 

The skills developer(s) will then install (and/or update) the plugin in Claude CoWork and will run manual tests to make sure the skills work as expected.
