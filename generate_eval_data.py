#!/usr/bin/env python3
"""
Script to generate 500 evaluation examples for the JSONL file
"""

import json
import random
from typing import List, Dict, Any

# Technology skills and their variations
TECH_SKILLS = [
    "JavaScript Programming",
    "Python Development",
    "Docker Containerization",
    "React Frontend Development",
    "Node.js Backend Development",
    "AWS Cloud Services",
    "Azure Cloud Platform",
    "Kubernetes Container Orchestration",
    "MongoDB Database Management",
    "PostgreSQL Database Administration",
    "GraphQL API Development",
    "REST API Design",
    "Machine Learning",
    "DevOps Engineering",
    "CI/CD Pipeline Management",
    "Git Version Control",
    "Linux System Administration",
    "Angular Framework",
    "Vue.js Development",
    "TypeScript Programming",
    "Java Enterprise Development",
    "C# .NET Development",
    "Spring Boot Framework",
    "Django Web Framework",
    "Flask Microframework",
    "Redis Caching",
    "RabbitMQ Message Queuing",
    "Apache Kafka Streaming",
    "Elasticsearch Search Engine",
    "Terraform Infrastructure as Code",
    "Ansible Configuration Management",
    "Jenkins Automation",
    "Prometheus Monitoring",
    "Grafana Visualization",
    "Microservices Architecture",
    "Event-Driven Architecture",
    "Software Testing",
    "API Testing",
    "Performance Testing",
    "Security Testing",
    "Agile Development",
    "Scrum Methodology",
    "Code Review Process",
    "Database Design",
    "System Design",
    "Network Security",
    "OAuth Authentication",
    "Backup and Recovery",
    "Load Balancing",
    "Content Delivery Networks",
]


def generate_ai_intro_message(skill_name: str) -> str:
    """Generate the standardized AI introduction message"""
    return f"""Expertise Levels in {skill_name}
Welcome! In this discussion, we will explore the various expertise levels related to the skill of {skill_name}. Understanding these levels will help you select the appropriate expertise that aligns with your current knowledge and experience.

Here are the available expertise grades:

Not Informed: You have no prior knowledge of the topic.
Informed Basics: You understand the basic concepts of {skill_name}.
Informed in Details: You have a deeper understanding of the strategies involved.
Practice and Lab Examples: You can apply your knowledge through practical examples and lab work.
Production Maintenance: You are capable of maintaining {skill_name.lower()} systems in a production environment.
Production from Scratch: You can set up {skill_name.lower()} systems from the ground up.
Educator/Expert: You possess extensive knowledge and can teach others about {skill_name}.
Consider your current level of understanding and experience to choose the expertise that best fits you. This will enhance your learning and engagement in our discussion!"""


def generate_conversation_templates():
    """Generate various conversation templates for different levels"""
    templates = {
        1: {  # Not Informed
            "user_responses": [
                "I have no experience with this technology. Where should I start?",
                "I've heard about this but never used it. Can you explain the basics?",
                "This is completely new to me. What's the learning curve like?",
                "I'm starting from zero. Is this difficult to learn?",
                "Never worked with this before. What are the prerequisites?",
                "I'm a complete beginner. What should I know first?",
                "No experience at all. Is this widely used in the industry?",
                "I'm just starting my journey with this. Any recommendations?",
                "Complete newbie here. How long does it take to learn?",
                "I've never touched this technology. What's it used for?",
            ],
            "ai_follow_ups": [
                "That's a great starting point! Everyone begins somewhere. This technology is widely used in the industry and has excellent learning resources available.",
                "No problem at all! Starting fresh means you can learn the best practices from the beginning without any bad habits to unlearn.",
                "Excellent question! The learning curve is manageable with consistent practice and the right resources. Let me help you understand the basics.",
                "Perfect place to start! This technology has a supportive community and plenty of learning materials to help you get started.",
                "That's completely normal! Many successful developers started exactly where you are. The key is taking that first step.",
                "Great mindset for learning! This technology is very beginner-friendly and has extensive documentation to guide you.",
                "Wonderful starting point! This skill is in high demand and learning it will definitely benefit your career growth.",
                "That's the right attitude! Starting with fundamentals will give you a strong foundation for advanced concepts later.",
                "Perfect! Being honest about your starting point helps me provide the most relevant guidance for your learning journey.",
                "Excellent place to begin! This technology is essential in modern development and you'll find it very rewarding to learn.",
            ],
        },
        2: {  # Informed Basics
            "user_responses": [
                "I understand the basic concepts but haven't applied them practically yet.",
                "I've read about this and watched some tutorials, but no hands-on experience.",
                "I know the theory but haven't built anything real with it.",
                "I've done some online courses but need more practice.",
                "I understand the fundamentals but struggle with implementation.",
                "I've been studying this for a few weeks but haven't used it professionally.",
                "I know what it is and how it works in theory, but limited practical experience.",
                "I've experimented with basic examples but nothing complex.",
                "I understand the core concepts but need more hands-on experience.",
                "I've completed some tutorials but haven't applied it to real projects.",
            ],
            "ai_follow_ups": [
                "That's a solid foundation! Understanding the theory is crucial. The next step is applying that knowledge through practice.",
                "Great start! Theoretical knowledge is important, and now you're ready to gain practical experience through small projects.",
                "Perfect position to be in! Your theoretical understanding will make the practical application much smoother.",
                "Excellent foundation! Theory-first learning often leads to better understanding when you start implementing.",
                "That's a common and valuable learning path! Your theoretical knowledge will guide you well in practical applications.",
                "Good approach! Having the conceptual understanding first will make your practical journey more effective.",
                "That's a strong starting point! Your theoretical knowledge puts you ahead of many beginners.",
                "Perfect! Understanding the why before the how is a great learning strategy that will serve you well.",
                "Excellent foundation! Your theoretical knowledge will help you avoid common pitfalls when you start practicing.",
                "Great preparation! Your conceptual understanding will make the transition to practical application much easier.",
            ],
        },
        3: {  # Informed in Details
            "user_responses": [
                "I've built a few small projects and understand the architecture patterns.",
                "I've used this in side projects and understand most of the concepts.",
                "I have some practical experience but mostly with basic implementations.",
                "I've worked through several tutorials and built some demo applications.",
                "I understand the advanced concepts but haven't used them in production.",
                "I've experimented with different approaches and understand the trade-offs.",
                "I've built some personal projects and understand the ecosystem.",
                "I have good theoretical knowledge and some practical experience.",
                "I've used this for hobby projects and understand the best practices.",
                "I've explored different features and understand when to use them.",
            ],
            "ai_follow_ups": [
                "That's excellent progress! Building projects and understanding architecture shows real practical knowledge.",
                "Great development! Side projects are a fantastic way to explore technology and build deeper understanding.",
                "Perfect! Basic implementations are often the most important to master thoroughly.",
                "Wonderful experience! Demo applications help you understand the full development cycle.",
                "That's a smart approach! Understanding advanced concepts prepares you for complex scenarios.",
                "Excellent! Understanding trade-offs shows you're thinking like an experienced developer.",
                "Great exploration! Understanding the ecosystem is crucial for making informed decisions.",
                "Perfect combination! Theoretical knowledge with practical experience is the ideal learning approach.",
                "Excellent application! Hobby projects let you experiment freely and learn best practices.",
                "That's advanced thinking! Understanding when to use different features shows deep comprehension.",
            ],
        },
        4: {  # Practice and Lab Examples
            "user_responses": [
                "I've completed several complex projects and feel comfortable with most features.",
                "I use this regularly in my work and can solve most problems independently.",
                "I've built production-ready applications but haven't deployed them yet.",
                "I'm comfortable with advanced features and can debug complex issues.",
                "I've mentored others and can explain complex concepts clearly.",
                "I've worked on team projects and understand collaborative development.",
                "I can implement complex requirements and optimize performance.",
                "I've integrated this with other technologies and understand the ecosystem.",
                "I'm comfortable with testing and can write maintainable code.",
                "I've worked on both frontend and backend implementations.",
            ],
            "ai_follow_ups": [
                "Outstanding! Complex projects and feature comfort demonstrate solid practical expertise.",
                "Excellent! Regular professional use and independent problem-solving show strong competency.",
                "Great preparation! Building production-ready applications shows you understand quality standards.",
                "Perfect! Advanced feature comfort and debugging skills are hallmarks of practical expertise.",
                "Wonderful! Mentoring others and explaining concepts clearly shows mastery of the subject.",
                "Excellent! Team collaboration and understanding group development practices are crucial skills.",
                "Outstanding! Complex implementation and performance optimization show advanced practical knowledge.",
                "Perfect! Integration experience and ecosystem understanding demonstrate comprehensive knowledge.",
                "Excellent! Testing practices and maintainable code show professional-level understanding.",
                "Great versatility! Full-stack experience shows comprehensive understanding of the technology.",
            ],
        },
        5: {  # Production Maintenance
            "user_responses": [
                "I maintain production systems and handle deployment issues regularly.",
                "I'm responsible for monitoring and troubleshooting production environments.",
                "I've migrated legacy systems and managed production deployments.",
                "I handle security updates and performance optimization in production.",
                "I'm on-call for production issues and can resolve them quickly.",
                "I've scaled production systems and handled high-traffic scenarios.",
                "I implement monitoring and alerting for production systems.",
                "I've managed database migrations and zero-downtime deployments.",
                "I handle backup and recovery procedures for production systems.",
                "I've optimized production performance and reduced system costs.",
            ],
            "ai_follow_ups": [
                "Excellent! Production maintenance and deployment management show real operational expertise.",
                "Outstanding! Monitoring and troubleshooting production systems requires advanced skills.",
                "Perfect! Migration experience and deployment management demonstrate comprehensive knowledge.",
                "Great! Security and performance management in production shows professional competency.",
                "Excellent! On-call responsibility and quick issue resolution show operational mastery.",
                "Outstanding! Scaling and high-traffic management demonstrate advanced production skills.",
                "Perfect! Monitoring and alerting implementation shows proactive operational thinking.",
                "Excellent! Database migrations and zero-downtime deployments require sophisticated knowledge.",
                "Great! Backup and recovery procedures show comprehensive operational understanding.",
                "Outstanding! Performance optimization and cost reduction show business-aware technical leadership.",
            ],
        },
        6: {  # Production from Scratch
            "user_responses": [
                "I've designed and built complete production systems from the ground up.",
                "I architect solutions and make technology decisions for the entire team.",
                "I've set up CI/CD pipelines and established development workflows.",
                "I design system architecture and make infrastructure decisions.",
                "I've built microservices architectures and distributed systems.",
                "I establish coding standards and review architectural decisions.",
                "I've designed APIs and integration patterns used by multiple teams.",
                "I mentor teams on best practices and architectural patterns.",
                "I've built scalable systems that handle millions of requests.",
                "I make technology choices and evaluate new tools for the organization.",
            ],
            "ai_follow_ups": [
                "Exceptional! Building complete production systems from scratch shows architectural expertise.",
                "Outstanding! Making technology decisions and architecting solutions demonstrates leadership.",
                "Excellent! CI/CD setup and workflow establishment show comprehensive DevOps knowledge.",
                "Perfect! System architecture and infrastructure decisions require deep technical understanding.",
                "Great! Microservices and distributed systems design show advanced architectural skills.",
                "Excellent! Establishing standards and reviewing architecture demonstrates technical leadership.",
                "Outstanding! Multi-team API design and integration patterns show enterprise-level thinking.",
                "Perfect! Team mentoring and pattern guidance demonstrate both technical and leadership skills.",
                "Exceptional! Building scalable, high-volume systems shows advanced production expertise.",
                "Excellent! Technology evaluation and organizational decision-making show strategic thinking.",
            ],
        },
        7: {  # Educator/Expert
            "user_responses": [
                "I teach this technology at conferences and write technical articles about it.",
                "I contribute to open source projects and help shape the technology's future.",
                "I've written books or created comprehensive training materials.",
                "I'm consulted by other organizations for complex architectural decisions.",
                "I've spoken at major conferences and am recognized as a thought leader.",
                "I contribute to the technology's documentation and best practices.",
                "I've trained hundreds of developers and created certification programs.",
                "I research new approaches and publish findings in the community.",
                "I've influenced the technology's roadmap and contributed to its evolution.",
                "I'm frequently quoted in technical publications and industry analyses.",
            ],
            "ai_follow_ups": [
                "Exceptional! Conference speaking and technical writing demonstrate true expertise and thought leadership.",
                "Outstanding! Open source contributions and technology influence show community leadership.",
                "Excellent! Creating comprehensive educational materials demonstrates mastery and teaching ability.",
                "Perfect! Cross-organizational consulting shows recognized expertise and trusted advisory status.",
                "Exceptional! Conference speaking and thought leadership recognition demonstrate industry expertise.",
                "Outstanding! Documentation and best practice contributions show community commitment.",
                "Excellent! Large-scale training and certification development demonstrate educational leadership.",
                "Perfect! Research and community publishing show innovation and knowledge advancement.",
                "Exceptional! Technology roadmap influence and evolution contributions demonstrate true expertise.",
                "Outstanding! Media recognition and industry analysis inclusion show established thought leadership.",
            ],
        },
    }
    return templates


def generate_final_ai_message(level: int, skill_name: str) -> str:
    """Generate the final AI message that confirms the level"""
    level_names = {
        1: "Not Informed",
        2: "Informed Basics",
        3: "Informed in Details",
        4: "Practice and Lab Examples",
        5: "Production Maintenance",
        6: "Production from Scratch",
        7: "Educator/Expert",
    }

    final_messages = {
        1: f"Perfect! Your honesty about being new to {skill_name} is valuable. Starting from Not Informed (Level 1) gives you a clear learning path ahead. Your expertise level has been recorded in your skill matrix. With dedication and practice, you'll progress through the levels quickly.",
        2: f"Excellent! Your theoretical understanding of {skill_name} concepts places you at Informed Basics (Level 2). Your foundation will make practical application much smoother. Your expertise level has been recorded in your skill matrix.",
        3: f"Great! Your practical experience with {skill_name} and understanding of detailed concepts confirms you're at Informed in Details (Level 3). Your expertise level has been recorded in your skill matrix.",
        4: f"Outstanding! Your complex project experience and comfort with advanced {skill_name} features clearly demonstrates Practice and Lab Examples (Level 4). Your expertise level has been recorded in your skill matrix.",
        5: f"Excellent! Your production maintenance experience and operational knowledge of {skill_name} systems confirms you're at Production Maintenance (Level 5). Your expertise level has been recorded in your skill matrix.",
        6: f"Exceptional! Your ability to build {skill_name} systems from scratch and make architectural decisions clearly demonstrates Production from Scratch (Level 6). Your expertise level has been recorded in your skill matrix.",
        7: f"Outstanding! Your teaching, contributions, and thought leadership in {skill_name} clearly demonstrate Educator/Expert (Level 7). Your expertise level has been recorded in your skill matrix. Your expertise benefits the entire community.",
    }

    return final_messages[level]


def generate_conversation(skill_name: str, level: int) -> List[Dict[str, str]]:
    """Generate a realistic conversation for a given skill and level"""
    templates = generate_conversation_templates()

    conversation = []

    # Start with AI introduction
    conversation.append(
        {"message": generate_ai_intro_message(skill_name), "role": "ai"}
    )

    # Add user response
    user_response = random.choice(templates[level]["user_responses"])
    conversation.append({"message": user_response, "role": "user"})

    # Add AI follow-up
    ai_follow_up = random.choice(templates[level]["ai_follow_ups"])
    conversation.append({"message": ai_follow_up, "role": "ai"})

    # Add 1-2 more exchanges for realism
    num_additional = random.randint(1, 2)
    for _ in range(num_additional):
        # Additional user message
        additional_user = random.choice(
            [
                f"How long did it take you to learn {skill_name}?",
                f"What resources would you recommend for {skill_name}?",
                f"Is {skill_name} still relevant in today's market?",
                f"What are the career prospects with {skill_name}?",
                f"Should I focus on {skill_name} or learn something else first?",
                f"How does {skill_name} compare to similar technologies?",
                f"What are the most important concepts in {skill_name}?",
                f"Are there any common mistakes beginners make with {skill_name}?",
                f"What projects should I build to practice {skill_name}?",
                f"How can I validate my {skill_name} knowledge?",
            ]
        )
        conversation.append({"message": additional_user, "role": "user"})

        # AI response
        additional_ai = random.choice(
            [
                f"Learning {skill_name} depends on your background and time commitment. With consistent practice, you can make significant progress.",
                f"The best resources for {skill_name} include official documentation, hands-on projects, and community forums.",
                f"{skill_name} remains highly relevant and continues to evolve with industry needs.",
                f"Career prospects with {skill_name} are excellent, with many opportunities in various industries.",
                f"The learning path depends on your goals, but {skill_name} is an excellent choice for your skill set.",
                f"Each technology has its strengths. {skill_name} excels in specific use cases and scenarios.",
                f"The most important {skill_name} concepts include understanding the fundamentals and practical application.",
                f"Common mistakes include rushing through basics and not practicing enough hands-on implementation.",
                f"Building real projects is the best way to practice {skill_name} and solidify your understanding.",
                f"Validation comes through practical projects, peer review, and continuous learning.",
            ]
        )
        conversation.append({"message": additional_ai, "role": "ai"})

    # Final AI message confirming the level
    conversation.append(
        {"message": generate_final_ai_message(level, skill_name), "role": "ai"}
    )

    return conversation


def generate_example(index: int) -> Dict[str, Any]:
    """Generate a single evaluation example"""
    # Random selection of parameters
    user_id = random.randint(1, 1000)
    skill_id = random.randint(1, 50)
    grade_id = random.randint(1, 7)
    skill_name = random.choice(TECH_SKILLS)

    # Generate conversation
    chat_messages = generate_conversation(skill_name, grade_id)

    return {
        "discrepancy": {"grade_id": grade_id, "skill_id": skill_id, "user_id": user_id},
        "guidance": [],
        "next_steps": [],
        "messages": [],
        "chat_messages": chat_messages,
    }


def generate_all_examples(num_examples: int = 500) -> List[Dict[str, Any]]:
    """Generate all evaluation examples"""
    examples = []

    for i in range(num_examples):
        example = generate_example(i)
        examples.append(example)

        # Progress indication
        if (i + 1) % 50 == 0:
            print(f"Generated {i + 1} examples...")

    return examples


def main():
    """Main function to generate and save evaluation data"""
    print("Generating 500 evaluation examples...")

    examples = generate_all_examples(500)

    # Write to JSONL file
    output_file = "/Users/danijeldjuric/Desktop/Projects/Solutions/l2work/test_data/evaluation.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"Successfully generated 500 examples and saved to {output_file}")
    print(f"File size: {len(examples)} examples")

    # Print some statistics
    grade_counts = {}
    for example in examples:
        grade = example["discrepancy"]["grade_id"]
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    print("\nGrade distribution:")
    for grade in sorted(grade_counts.keys()):
        print(f"  Level {grade}: {grade_counts[grade]} examples")


if __name__ == "__main__":
    main()
