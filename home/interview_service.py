import json

class InterviewService:
    def __init__(self):
        pass

    def parse_questions(self, content, num_questions, generic_questions):
        try:
            questions = json.loads(content)
            return questions[:num_questions]
        except json.JSONDecodeError:
            questions = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith(('Here', 'These', 'The following')):
                    continue

                first_space_index = line.find(' ')
                is_list_item = False
                clean_line = line

                if first_space_index > 0:
                    prefix = line[:first_space_index]
                    if prefix.rstrip('.').rstrip(')').isdigit() or prefix in ['-', '*', '•']:
                        is_list_item = True
                        potential_question = line[first_space_index + 1:].strip()
                        if potential_question:
                            clean_line = potential_question

                if is_list_item:
                    if clean_line != line:
                        questions.append(clean_line)
                else:
                    is_likely_unstyled_list = line.strip().startswith( ('-','*','•') ) or \
                                            (first_space_index > 0 and line[:first_space_index].rstrip('.').rstrip(')').isdigit())
                    if not is_likely_unstyled_list:
                        questions.append(clean_line)

            return questions[:num_questions] if questions else generic_questions

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            return "generic_feedback"

        return generic_questions