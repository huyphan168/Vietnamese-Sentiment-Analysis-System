const user = require("../models/user");
const User = require("../models/user");

exports.showCam = async (email) => {
    let user_content = {}
    user_content = await User.find({email: email});
    console.log(user_content);
    return user_content;
}