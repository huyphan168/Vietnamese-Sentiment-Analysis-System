const express = require("express");
const { showCampaign, showCam } = require("../controllers/showCampaign");
const router = express.Router();

router.get("/showCampaign/:email", async (req, res) => {
  let email = req.params.email
  campaigns = await showCam(email);
  res.json({
    "campaign": campaigns,
  });
});

module.exports = router;



// db.users.insertOne({ "email":"anh", "campaigns": [1, 2, 3]})