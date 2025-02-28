const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to log incoming requests
app.use((req, res, next) => {
    console.log(`${req.method} request for '${req.url}'`);
    next();
});


// Middleware
app.use(bodyParser.json());
app.use(express.static('public'));

app.post('/query', async (req, res) => {
    const userQuery = req.body.query; // Removed optional chaining
    // Check if the request is for conversation handling
    if (req.body.isConversation) { // Removed optional chaining
        const conversationResponse = await axios.post('http://localhost:5000/api/received_item', { statement: userQuery });
        return res.json(conversationResponse.data);
    }



    try {
        // Send the query to the NLU model (replace with actual endpoint)
        const response = await axios.post('http://localhost:5000/nlu', { query: userQuery }); // This line can remain for other queries

        res.json(response.data);
    } catch (error) {
        console.error('Error processing query:', error);
        res.status(500).json({ error: 'Failed to process query' });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
