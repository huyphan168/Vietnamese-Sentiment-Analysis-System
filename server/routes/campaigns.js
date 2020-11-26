const express = require("express");
const { createOrUpdateCampaign } = require("../controllers/campaign");

const router = express.Router();

router.post("/campaign", createOrUpdateCampaign);

module.exports = router;
