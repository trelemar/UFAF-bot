def isLeagueOwner(user):
    owner = False
    for role in user.roles:
        if role.name == "League Owner":
            owner = True
    return owner


def is_interaction_from_original_author(interaction):
    '''
    original_message = interaction.message
    print(original_message)
    original_author = original_message.author
    return interaction.user.id == original_author.id
    '''
    return True