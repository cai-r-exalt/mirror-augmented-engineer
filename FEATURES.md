# Bel'Air's Buvette Features

Welcome to the Bel'Air's Buvette project! This document outlines the key features and functionalities of the backend system designed to manage drinks and snacks efficiently.

## Features

### As a festival goer, I want to consult the remaining balance of my tokens

Rules:
- A festival goer has two types of tokens: drink tokens and snack tokens
- A festival goer can have zero or more drink tokens
- A festival goer can have zero or more snack tokens
- A festival goer cannot have a negative balance of tokens
- A festival goer gets 9 food tokens and 6 drink tokens per day of festival
- Unspent tokens are not carried over to the next day

### As a festival goer, I want to place an order for a drink

Rules:
- A drink can be either alcoholic or non-alcoholic
- A non-alcoholic drink costs no drink tokens
- A normal alcoholic drink costs one drink token
- A premium alcoholic drink costs two drink tokens

### As a festival goer, I want to place an order for food

Rules:
- There are two types of food items: snack and meals
- Meals cost 3 food tokens
- Snacks cost 1 food token

### As a festival goer, I want to be able to order multiple items in a single order

Rules:
- A festival goer can order multiple items in a single order
- The total cost of the order must not exceed the festival goer's token balance on either drink or food tokens
- The order is rejected if any requested item is out of stock

### As a bartender, I want to manage the inventory of drinks and food items

Rules:
- Each drink item has a stock quantity that can be tracked and updated
- Each food item (snack or meal) has a stock quantity that can be tracked and updated
- The stock quantity cannot be negative
- When an order is placed, the stock for all requested items must be checked
- If any item in the order is out of stock, the entire order is rejected and no tokens are deducted
- Stock is decremented only when an order is successfully placed and acknowledged

### As a group of festival goers, we want to be able to pool our tokens to place a group order

Rules:
- The group order can be placed only if the pooled tokens are sufficient to cover the total cost
- Each festival goer can contribute any amount of their tokens to the group order
- The group order will be treated as a single order and will follow all the same rules

### As a festival goer, I want to be able to change my order

Rules:
- An order can be changed only if it has not yet been acknowledged by the bartender
- The festival goer can add or remove items from the order
- The total cost of the modified order must not exceed the festival goer's token balance on either drink or food tokens
- If the order is already acknowledged, the bartender must be notified of the requested changes

### As a festival goer, I want to be able to cancel my order

Rules:
- An order can be cancelled only if it has not yet been acknowledged by the bartender
- Upon cancellation, the tokens used for the order are refunded to the festival goer's balance
- The festival goer receives a confirmation of the cancellation

### As a bartender, I want to acknowledge an order so that the festival goer knows their order is being prepared, and provide an estimated time of readiness

Rules:
- Once an order is acknowledged, the festival goer is notified that their order is being prepared
- An estimated time of readiness is provided to the festival goer based on current workload and order
- The estimated time of readiness is calculated as follows:
  - For orders containing only non-alcoholic drinks: 1 minute per type of drink (e.g. 3 different non-alcoholic drinks = 3 minutes)
  - For orders containing normal alcoholic drinks: 2 minutes per drink
  - For orders containing premium alcoholic drinks: 3 minutes per drink
  - For mixed orders, the total time is the sum of the times for each type of order (non-alcoholic, normal alcoholic, premium alcoholic)
  - For orders containing snacks: 2 minutes per snack type
  - For orders containing meals: 10 minutes per type of meal plus the longest preparation time of any drink in the order

The idea being that meals take longer to prepare, but can be prepared in parallel with drinks.
Orders containing the same type of items are prepared together, so only the number of different types of items matters for preparation time.

### As a bartender, I want to mark an order as ready so that the festival goer knows their order is ready for pickup

Rules:
- An order can only be marked as ready if there is enough prepared items to fulfil the order
- Once the order is marked as ready, the festival goer is notified they can pick up their order

### As a bartender, upon receiving a request to change an acknowledged order, I want to review and approve or reject the changes

Rules:
- The requested change can only be accepted if at least one of the items already prepared can be transferred to another order
- Once the requested change is accepted, the festival goer is notified of the updated estimated time of readiness

### As a festival goer, I want to transfer tokens to another festival goer

Rules:
- The festival goer can transfer up to three tokens of each type to another festival goer
- The token transfer must be confirmed by the recipient festival goer
- The token balance of the transferring festival goer cannot become negative as a result of the transfer

### As the bartender, I want regular notifications sent to the festival goers to remind them to drink water, because it's hot out there!

Rules:
- Every hour, a notification is sent to all festival goers reminding them to drink water
- The notification includes a friendly message and encourages responsible drinking
- If a festival goer has drunk more than 3 alcoholic drinks in the past hour, the notification should be sent more frequently, every 30 minutes
- The notification should be sent only between 11:00 AM and 7:00 PM each day of the festival (because past 7:00 PM, it's time to party, and before 11:00 AM, hopefully, no one is drinking anything but fruit juices!)
