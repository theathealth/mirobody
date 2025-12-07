from mirobody.server import Server

#-----------------------------------------------------------------------------

async def main():
    yaml_filenames = ['config/config.yaml']
    await Server.start(yaml_filenames)

#-----------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

#-----------------------------------------------------------------------------
