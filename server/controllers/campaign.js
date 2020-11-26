const { createIndexes } = require("../models/user");
const User = require("../models/user");

exports.createOrUpdateCampaign = async (req, res) => {
  const {
    campaignId,
    email,
    app_secret,
    app_id,
    page_id,
    access_token,
    Keyword,
    flag,
    created_time,
    status,
  } = req.body;
  console.log("email ", email);
  console.log("email ", req.body.email);

  await User.findOneAndUpdate(
    { email: email },
    {
      $push: {
        campaigns: {
          campaignId:campaignId,
          result:{
          },
          page_info:{
            app_id: app_id,
            app_secret: app_secret,
            access_token: access_token,
            page_id: page_id,
            keyword: Keyword,
          },
          flag: flag,
          created_time: created_time,
          status: status,
        },
      },


    },{new: true }
  );
  

  res.json("Update success");
};
