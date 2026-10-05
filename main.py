from config import Config
from notion.page_client import NotionPageClient
from notion.story_util import StoryContext, MarkdownToNotionConverter
from tool import utils
from LLM.factory import llm_factory

config = Config.from_env()


def build_context(chapters=4):
    notion_client = NotionPageClient(config.notion)
    story_context = StoryContext(notion_client)
    print("\n" + "="*60)
    print("Building context...")
    
    context = story_context.get_context_for_generation(
        strategy="full", 
        num_chapters=chapters
    )
    
    print(f"\nContext length: {len(context)} characters")
    utils.save_to_file(
        content=context,
        filename="context.md",
        output_dir="prompts",
    )
    


def gen_text():
    print("\n" + "="*60)
    print("Generating text...")
    llm = llm_factory(config.llm)
    new_content = llm.generate_text(
        user_prompt=utils.load_prompt_from_file(filename="gen_prompt.md"),
        story_context=utils.load_prompt_from_file(filename="context.md"),
        system_prompt=utils.load_prompt_from_file(filename="sys_prompt.md"),
    )

    utils.save_to_file(new_content)

def upload_page():
    notion_client = NotionPageClient(config.notion)
    converter = MarkdownToNotionConverter(notion_client)
    print("\n" + "="*60)
    print("Fetching page...")

    import os
    file_path = 'outputs/'
    file_name = os.listdir(file_path)[-1]
    with  open(os.path.join(file_path + file_name), 'r', encoding='utf-8') as f:
        upload_content = f.read()

    
    page = converter.create_page_from_markdown(
        title='New Page',
        markdown_content=upload_content,
    )
    
def asking_opt():
    opt =int(input("\
        1. Build context \n\
        2. Generate content\n\
        3. Upload Page\n "))
    match opt:
        case 1: build_context()
        case 2: gen_text()
        case 3: upload_page()

def main():
    # build_context(6)
    
    gen_text()

    # upload_page()
    

if __name__ == "__main__":
    main()
