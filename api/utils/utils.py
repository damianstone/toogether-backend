def binary_search(elements, target):
    start = 0
    end = len(elements) - 1

    while start <= end:
        mid = start + (end - start) // 2

        if elements[mid] > target:
            end = mid - 1
        elif elements[mid] < target:
            start = mid + 1
        else:
            return mid

    return -1


# create a function that lists the likes ids that not belong to a any match model in django rest framework
def get_likes_ids_not_in_match(user_id):
    # get all the likes ids that belong to a match
    match_ids = Match.objects.filter(Q(user_1=user_id) | Q(user_2=user_id)).values_list(
        "user_1", "user_2"
    )
    # get all the likes ids that not belong to a match
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .values_list("liked_user_id", flat=True)
    )
    return likes_ids


# create a function that lists the likes ids that not belong to a any match model in django rest framework
def get_likes_ids_not_in_match_and_not_in_block(user_id):
    # get all the likes ids that belong to a match
    match_ids = Match.objects.filter(Q(user_1=user_id) | Q(user_2=user_id)).values_list(
        "user_1", "user_2"
    )
    # get all the likes ids that not belong to a match
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .values_list("liked_user_id", flat=True)
    )
    # get all the likes ids that not belong to a block
    block_ids = Block.objects.filter(user_id=user_id).values_list(
        "blocked_user_id", flat=True
    )
    # get all the likes ids that not belong to a match and not belong to a block
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .exclude(liked_user_id__in=block_ids)
        .values_list("liked_user_id", flat=True)
    )
    return likes_ids



# create a function that lists the likes ids that not belong to a any match model in django rest framework
def get_likes_ids_not_in_match_and_not_in_block_and_not_in_report(user_id):
    # get all the likes ids that belong to a match
    match_ids = Match.objects.filter(Q(user_1=user_id) | Q(user_2=user_id)).values_list(
        "user_1", "user_2"
    )
    # get all the likes ids that not belong to a match
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .values_list("liked_user_id", flat=True)
    )
    # get all the likes ids that not belong to a block
    block_ids = Block.objects.filter(user_id=user_id).values_list(
        "blocked_user_id", flat=True
    )
    # get all the likes ids that not belong to a match and not belong to a block
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .exclude(liked_user_id__in=block_ids)
        .values_list("liked_user_id", flat=True)
    )
    # get all the likes ids that not belong to a report
    report_ids = Report.objects.filter(user_id=user_id).values_list(
        "reported_user_id", flat=True
    )
    # get all the likes ids that not belong to a match and not belong to a block and not belong to a report
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .exclude(liked_user_id__in=block_ids)
        .exclude(liked_user_id__in=report_ids)
        .values_list("liked_user_id", flat=True)
    )
    return likes_ids


# create a function that lists the likes ids that not belong to a any match model in django rest framework
def get_likes_ids_not_in_match_and_not_in_block_and_not_in_report_and_not_in_like(
    user_id,
):
    # get all the likes ids that belong to a match
    match_ids = Match.objects.filter(Q(user_1=user_id) | Q(user_2=user_id)).values_list(
        "user_1", "user_2"
    )
    # get all the likes ids that not belong to a match
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .values_list("liked_user_id", flat=True)
    )
    # get all the likes ids that not belong to a block
    block_ids = Block.objects.filter(user_id=user_id).values_list(
        "blocked_user_id", flat=True
    )
    # get all the likes ids that not belong to a match and not belong to a block
    likes_ids = (
        Like.objects.filter(user_id=user_id)
        .exclude(liked_user_id__in=match_ids)
        .exclude(liked_user_id__in=block_ids)
        .values_list("liked_user_id", flat=True)
    )


# create a model class in django rest for a match between two users
class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2')
    match_date = models.DateTimeField(auto_now_add=True)
    match_status = models.BooleanField(default=False)

    def __str__(self):
        return self.user1.username + ' ' + self.user2.username