# TopEventNite

![TopEventNite Mockup](assets/images/mockup.png)
<p align="center">
  <a href="https://topeventnite-vanessa-f8272a2fa386.herokuapp.com/" target="_blank">
    View Live Website
  </a>
</p>

## Table of Contents

- [Project Overview](#project-overview)

- [UX / UI Design](#ux--ui-design)
  - [User Experience (UX)](#user-experience-ux)
  - [User Interface (UI)](#user-interface-ui)
  - [Accessibility](#accessibility)
  - [User Stories](#user-stories)
  - [Design Choices](#design-choices)
    - [Colours](#colours)
    - [Typography](#typography)
    - [Layout and Structure](#layout-and-structure)
    - [Imagery](#imagery)

- [Core Functionality](#core-functionality)
  - [Authentication System](#authentication-system)
  - [Event Management](#event-management)
  - [Booking System](#booking-system)
  - [Payment Integration (Stripe)](#payment-integration-stripe)

- [Database Design](#database-design)

- [Built With](#built-with)

- [Testing](#testing)
  - [Manual Testing](#manual-testing)
  - [Responsive Testing](#responsive-testing)
  - [Deployment Testing](#deployment-testing)
  - [Validation](#validation)
    - [HTML Validation](#html-validation)
    - [CSS Validation](#css-validation)
    - [Accessibility Testing](#accessibility-testing)
  - [Known Bugs](#known-bugs)

- [Deployment](#deployment)

- [Security](#security)

- [Future Features](#future-features)

- [Credits](#credits)

- [AI Tool Usage & Reflection](#ai-tool-usage--reflection)

## Project Overview

TopEventNite is a full-stack event management and ticket booking platform designed to allow organisers to create and manage events, while attendees can browse, book, and manage their tickets in a simple and user-friendly way.

The main purpose of the application is to provide a streamlined experience for both event organisers and attendees. Organisers can easily create, edit, and delete events, while attendees can explore available events, complete bookings through an integrated payment system, and manage their bookings in one place.

The idea for TopEventNite was inspired by modern event platforms that combine event discovery with seamless ticket booking. The focus of this project was to create a system that not only supports core functionality such as CRUD operations and authentication, but also incorporates real-world features such as payment integration, booking validation, and role-based access control.

This project was built using Python and the Django framework for the backend, with PostgreSQL for database management. Stripe was integrated to handle secure payment processing, and Cloudinary was used for image uploads. The front-end was developed using HTML, CSS, and JavaScript, with a strong emphasis on responsive design and user experience.

TopEventNite demonstrates the development of a full-stack application that connects front-end interfaces with back-end logic, handles user authentication and permissions, manages data efficiently, and provides a complete end-to-end user journey from event creation to booking confirmation.