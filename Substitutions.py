import Persistence
from DataFrame import DataFrame

LEFT_CURLY_BRACE = '{'
RIGHT_CURLY_BRACE = '}'


class Substitutions:
    def __init__(self):
        file_path = Persistence.private_file_path("Substitutions.csv")
        self.substitutions = DataFrame(["SHORT", "LONG"], file_path)

    def substitute(self, text, substitutions=None):
        result = text
        for key in self.substitutions.df["SHORT"]:
            while key in result:
                replacement = self.substitutions.get_value("SHORT", key, "LONG")
                result = result.replace(f"{key}", replacement)

        while True:
            if "{" in result and "}" in result:
                key = result[result.find("{") + 1:result.find("}")]
                substitution = substitutions[key]
                result = result.replace(f"{LEFT_CURLY_BRACE}{key}{RIGHT_CURLY_BRACE}", substitution)
            else:
                break

        return result


if __name__ == '__main__':
    s = Substitutions()
