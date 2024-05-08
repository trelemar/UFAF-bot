def isLeagueOwner(user):
    owner = False
    for role in user.roles:
        if role.name == "League Owner":
            owner = True
    return owner


def is_interaction_from_original_author(ctx, interaction):
    return ctx.author.id == interaction.user.id