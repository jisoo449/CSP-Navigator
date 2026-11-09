"""서비스 계층 오류."""


class ServiceError(Exception):
    """화면에 그대로 보여 줘도 되는 사용자용 문구를 담는 오류. (NF2004)

    API 키, 프롬프트 전문, 오류 추적 정보는 user_message에 넣지 않는다.
    """

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message
