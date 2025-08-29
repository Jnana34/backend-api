from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.bot.utils import nl_to_sql_and_template, run_sql


class ChatbotQueryView(APIView):
    def post(self, request):
        try:
            question = request.data.get("question", "")
            if not question:
                return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get SQL or direct answer
            parsed = nl_to_sql_and_template(question)

            if parsed["mode"] == "sql":
                try:
                    result = run_sql(parsed["sql"])
                    flat = ", ".join(str(r[0]) for r in result) if result else "not found"
                    answer = parsed["template"].replace("{{rows}}", flat).replace("{rows}", flat)
                except Exception as e:
                    return Response({"error": f"SQL execution failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                answer = parsed["answer"]

            return Response({
                "question": question,
                "mode": parsed["mode"],
                "sql": parsed.get("sql"),
                "answer": answer
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
