// text_correction.baml - BAML file for text correction and regeneration

// Function for regenerating a specific part of a text while maintaining context

class RegeneratedText {
  regenerated_text string @description("Regenerated text that replaces the selected text")
}

function RegenerateText(
  original_text: string @description("The complete original text") ,
  selected_text: string @description("The portion of text to be modified"),
  user_profile: string? @description("User profile/CV for context"),
  job_description: string? @description("Job description for context"),
  user_feedback: string? @description("User feedback about what to change")
) -> RegeneratedText {
  client LLMFallback
  prompt #"# Intelligent Text Regeneration

## Objective
Regenerate a specific part of the text while considering the global context and user feedback.

## Critical Rules
1. Modify ONLY the selected portion of text
2. Maintain coherence with the rest of the text
3. Preserve the original style and tone
4. Respect the approximate length (+/- 20%)
5. Ensure smooth transitions

## Detailed Instructions

1. **Context Analysis**
   - Understand the position of the selected text within the whole document
   - Identify the style and tone of the document
   - Evaluate elements to improve based on feedback
   {% if user_profile %}
   - Verify consistency with the user profile
   {% endif %}
   {% if job_description %}
   - Ensure alignment with the job description
   {% endif %}

2. **Rewriting Rules**
   - Preserve the existing grammatical structure
   - Maintain the language level
   - Avoid repetitions with the rest of the text
   - Enhance clarity and precision
   - Adapt content according to user feedback

3. **Output Validation**
   - Check transition fluidity
   - Confirm message coherence
   - Ensure the text integrates naturally

## Provided Data

Complete Text:
{{ original_text }}

Text to Modify:
{{ selected_text }}

{% if user_feedback %}
User Feedback:
{{ user_feedback }}
{% endif %}

{% if user_profile %}
User Profile:
{{ user_profile }}
{% endif %}

{% if job_description %}
Job Description:
{{ job_description }}
{% endif %}

{# special macro to print the output schema instructions #}
{{ ctx.output_format }}
"#
}

// Tests for different scenarios
test BasicTextCorrectionTest {
  functions [RegenerateText]
  args {
    original_text #"Je suis un développeur passionné avec 5 ans d'expérience. J'aime beaucoup la programmation et je code tout le temps. Je suis très motivé et j'apprends rapidement."#
    selected_text #"J'aime beaucoup la programmation et je code tout le temps."#
    user_feedback "Cette partie sonne trop informelle et répétitive"
  }
}

test CoverLetterCorrectionTest {
  functions [RegenerateText]
  args {
    original_text #"Je suis très intéressé par le poste d'ingénieur logiciel au sein de votre entreprise. Durant mes études, j'ai fait beaucoup de projets cool en programmation. Ces expériences m'ont permis de devenir un bon développeur."#
    selected_text #"Durant mes études, j'ai fait beaucoup de projets cool en programmation."#
    user_feedback "Rendre plus professionnel et ajouter des détails techniques"
    user_profile #"Formation: Master en Informatique
Compétences: Java, Python, React, Node.js
Projets: Développement d'une application web de gestion de projet"#
    job_description #"Recherche Ingénieur Logiciel
- Expertise en Java et React requise
- Expérience en développement web
- Capacité à gérer des projets complexes"#
  }
}

test TechnicalDetailsCorrectionTest {
  functions [RegenerateText]
  args {
    original_text #"Dans mon dernier projet, j'ai utilisé différentes technologies pour créer une application web. Le projet a été un succès et les utilisateurs étaient satisfaits. J'ai beaucoup appris durant ce développement."#
    selected_text #"j'ai utilisé différentes technologies pour créer une application web"#
    user_feedback "Spécifier les technologies utilisées et les résultats concrets"
    user_profile #"Expérience:
- Développement Full Stack avec React et Node.js
- Base de données MongoDB
- Tests avec Jest
- Déploiement sur AWS"#
  }
}

test LanguageStyleCorrectionTest {
  functions [RegenerateText]
  args {
    original_text #"Madame, Monsieur,

Je vous écris pour postuler au poste de développeur senior. Je suis trop motivé pour rejoindre votre équipe car vous êtes les meilleurs. J'ai vraiment envie de travailler avec vous.

Cordialement,"#
    selected_text #"Je suis trop motivé pour rejoindre votre équipe car vous êtes les meilleurs."#
    user_feedback "Le ton est trop familier et manque de professionnalisme"
  }
}

test MinimalCorrectionTest {
  functions [RegenerateText]
  args {
    original_text #"Le projet a été réalisé en utilisant diverses technologies."#
    selected_text #"diverses technologies"#
    user_feedback "Être plus spécifique"
  }
}

// English test examples
test EnglishCoverLetterTest {
  functions [RegenerateText]
  args {
    original_text #"I am writing to apply for the Software Engineer position at your company. I have been coding for many years and I really love it. I believe I would be a great addition to your team."#
    selected_text #"I have been coding for many years and I really love it."#
    user_feedback "Make this more professional and add specific technical details"
    user_profile #"Education: MSc in Computer Science
Skills: Java, Python, React, Node.js, AWS
Projects: Developed an e-commerce platform with 10,000+ users"#
    job_description #"Software Engineer Position
- 3+ years experience with Java and React
- Experience with cloud technologies
- Strong problem-solving skills"#
  }
}

test EnglishTechnicalTest {
  functions [RegenerateText]
  args {
    original_text #"In my previous role, I worked on several important projects. I used many different tools and technologies to solve complex problems. The results were very good and the client was happy."#
    selected_text #"I used many different tools and technologies to solve complex problems."#
    user_feedback "Add specific technologies and quantifiable results"
    user_profile #"Experience:
- Full Stack Developer at TechCorp (2018-2022)
- Technologies: React, Node.js, MongoDB, AWS
- Led a team of 5 developers"#
  }
} 