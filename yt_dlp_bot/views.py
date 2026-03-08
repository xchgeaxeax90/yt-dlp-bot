import discord

class PaginatedView(discord.ui.View):
    def __init__(self, items: list, items_per_page: int = 10):
        super().__init__(timeout=60)
        self.items = items
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page if items else 1
        self.message = None

    async def create_embed(self, page_items: list) -> discord.Embed:
        """Subclasses should override this to create the embed for the current page."""
        raise NotImplementedError("Subclasses must implement create_embed")

    async def get_current_page_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.items[start_idx:end_idx]
        return await self.create_embed(page_items)

    def update_buttons(self):
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= self.total_pages - 1)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=await self.get_current_page_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=await self.get_current_page_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass
