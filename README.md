Chatbot Project
Overview
This project is a Telegram Chatbot designed to engage users in a conversation, provide answers to their queries using Gemini-powered AI and save chat history in MongoDB. Additionally, the bot can accept images and files, analyze them, and reply with appropriate content. The bot can also perform web searches based on user queries.

Features
User Registration: Stores user information (first name, username, chat ID) in MongoDB.
Gemini-Powered Chat: Leverages the Gemini API (Google Generative AI) to respond to user queries.
Chat History Storage: Saves the chat history (user input and bot response) in MongoDB with timestamps.
File & Image Analysis: Accepts images (JPG, PNG, PDF) and provides a description of the content.
Web Search: Allows users to perform web searches via the chatbot interface.
Secure Payment Integration: (Optional) Integrated Razorpay API for payment-related tasks.
Technologies Used
Telegram Bot API: To handle bot-user interactions.
Gemini API: To generate content responses using AI.
MongoDB: To store user information and chat history.
Python: Main programming language for building the bot.
Flask (optional): For integrating the bot with web services, if required.
Heroku/Netlify (optional): For deployment.
