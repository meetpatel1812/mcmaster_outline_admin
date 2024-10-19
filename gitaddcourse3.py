import streamlit as st
import os
import json
from github import Github
import base64
import ast

# Set Page Configuration
st.set_page_config(page_title="Admin Course Management", layout="wide")

# Define categories, subcategories, and semesters for selection
course_type_options = [
    "Required core courses",
    "Professional Development course",
    "Core course",
    "Recommended Technical electives",
    "Cross-Disciplinary Elective Course",
    "Other elective course"
]

stream_options = [
    "Automotive Stream",
    "Automation and Smart Systems",
    "Digital Manufacturing",
    "Process Systems Stream",
    "All stream course"
]

semester_options = ["Fall", "Winter", "Summer"]

# GitHub repository details
github_token = st.secrets.get("GITHUB_TOKEN")
repo_name = "meetpatel1812/mcmaster_course_outline_app"
file_path = "pdf_data.py"  # Update this with the correct path in your repo

# Initialize GitHub instance
g = Github(github_token)
repo = g.get_repo(repo_name)

# Function to fetch courses from GitHub
def fetch_courses():
    contents = repo.get_contents(file_path)
    file_content = contents.decoded_content.decode("utf-8")
    
    # Safely parse the content to extract 'pdfs' list
    parsed_content = ast.parse(file_content)
    
    # Look for the 'pdfs' variable in the parsed content
    for node in parsed_content.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'pdfs':
                    return ast.literal_eval(node.value)
    return []

# Fetch existing courses from GitHub
try:
    courses = fetch_courses()
    if not courses:
        st.warning("No courses found in the repository.")
except Exception as e:
    st.error(f"Error loading courses from GitHub: {str(e)}")
    courses = []

# Course Addition, Modification, and Deletion Header
st.header("Admin Course Management")

# Course Addition Form
st.subheader("Add / Modify Course")
st.divider()

# Select course for modification
course_names = [course['name'] for course in courses]
selected_course_name = st.selectbox("Select a Course to Modify (or leave blank to add a new course)", [""] + course_names)
st.divider()

# If a course is selected, load its details for modification
if selected_course_name:
    selected_course = next((course for course in courses if course["name"] == selected_course_name), None)
    if selected_course:
        st.info(f"Modifying: {selected_course_name}")
        course_name = st.text_input("Course Name", selected_course['name'])
        course_label = st.text_input("Course Label", selected_course['label'])
        category = st.selectbox("Select Course Type", course_type_options, index=course_type_options.index(selected_course['category']))
        subcategory = st.selectbox("Select Stream", stream_options, index=stream_options.index(selected_course['subcategory']))
        semesters = st.multiselect("Select Semester(s)", semester_options, default=selected_course['semesters'])
        uploaded_file = st.file_uploader("Upload Course Outline PDF (leave blank to keep current)", type=["pdf"])
    else:
        st.error("Selected course not found.")
else:
    # Default empty form for new course
    course_name = st.text_input("Course Name")
    course_label = st.text_input("Course Label")
    category = st.selectbox("Select Course Type", course_type_options)
    subcategory = st.selectbox("Select Stream", stream_options)
    semesters = st.multiselect("Select Semester(s)", semester_options)
    uploaded_file = st.file_uploader("Upload Course Outline PDF", type=["pdf"])

# Submit button
submitted = st.button("Submit Course")

if submitted:
    # Ensure all fields are filled
    if not course_name or not course_label or not semesters:
        st.error("Please fill all fields.")
    else:
        # Prepare course data
        course_data = {
            "name": course_name,
            "label": course_label,
            "category": category,
            "subcategory": subcategory,
            "semesters": semesters,
            "file_path": f"Course/{category.replace(' ', '_')}/{uploaded_file.name if uploaded_file else selected_course['file_path'].split('/')[-1]}",
            "icon": ""
        }

        # Handle course addition or modification
        if selected_course_name:
            # Modify existing course
            st.info("Updating course information...")
            courses = [course_data if course['name'] == selected_course_name else course for course in courses]
        else:
            # Add new course
            courses.append(course_data)

        # Save the PDF file to GitHub (if a new file is uploaded)
        if uploaded_file:
            try:
                pdf_content = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
                pdf_github_path = f"Course/{category.replace(' ', '_')}/{uploaded_file.name}"

                try:
                    existing_file = repo.get_contents(pdf_github_path)
                    repo.update_file(
                        path=pdf_github_path,
                        message=f"Update PDF for {course_name}",
                        content=pdf_content,
                        sha=existing_file.sha
                    )
                except:
                    repo.create_file(
                        path=pdf_github_path,
                        message=f"Add PDF for {course_name}",
                        content=pdf_content
                    )
                st.success("PDF uploaded successfu
