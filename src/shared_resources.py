class SharedResources:
    @classmethod
    def set_body(cls, body):
        cls.body = body
        
    @classmethod
    def get_body(cls):
        assert cls.body is not None, 'Body not set'
        return cls.body

    @classmethod
    def set_total_cost_text(cls, total_cost_text):
        cls.total_cost_text = total_cost_text

    @classmethod
    def update_total_cost(cls, total_cost):
        cls.total_cost_text.value = f"Suma kosztów: {total_cost:.2f}"
        cls.total_cost_text.update()
