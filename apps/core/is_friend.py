from django.contrib.auth import get_user_model

User = get_user_model()

def are_friends(user1: User, user2: User) -> bool:
    """
    Check if two users are friends.
    Supports both direct ManyToMany relations (user.friends)
    and custom through Friendship models.
    """
    if not user1 or not user2:
        return False

    # Same user is not "friend"
    if user1 == user2:
        return False

    try:
        if hasattr(user1, "friends"):
            # Case 1: ManyToMany(User) direct relation
            if hasattr(user1.friends, "filter"):
                return user1.friends.filter(id=user2.id).exists()

            # Case 2: ManyToMany with through model
            elif hasattr(user1.friends, "through"):
                friendship_model = user1.friends.through
                return friendship_model.objects.filter(
                    user=user1, friend=user2
                ).exists()
    except Exception:
        return False

    return False
