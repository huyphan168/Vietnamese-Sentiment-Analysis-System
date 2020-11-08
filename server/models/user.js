const mongoose = require("mongoose");
const { ObjectId } = mongoose.Schema;

const userSchema = new mongoose.Schema(
  {
    name: String,
    email: {
      type: String,
      required: true,
      index: true,
    },
    status: {
      type: String,
      default: "ok",
    },
    campaigns: {
      type: Array,
      default: [],
    },
    address: String,
  },
  { timestamps: true }
);

module.exports = mongoose.model("User", userSchema);
