// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

import "@openzeppelin/contracts/access/Ownable.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface IFeeDistributor {
    function last_token_time() external view returns (uint256);

    function checkpoint_token() external;
}

contract RewardsManager is Ownable {
    using SafeERC20 for IERC20;

    /// @notice Timestamp of our most recent SCREAM payout.
    uint256 public lastPayoutTime = 1679525505;

    /// @notice Amount of our most recent SCREAM distribution.
    uint256 public lastPayoutAmount = 490e18;

    /// @notice Addresses that can trigger weekly payouts and checkpoints.
    mapping(address => bool) public authorizedAddresses;

    /// @notice This contract distributes our claims for veSCREAM holders.
    IFeeDistributor public constant feeDistributor =
        IFeeDistributor(0xae1BA6F7BAc58752e2B77923CF7a813153812619);

    /// @notice SCREAM is our fee (reward) token.
    IERC20 public constant scream =
        IERC20(0xe0654C8e6fd4D733349ac7E09f6f23DA256bF475);

    constructor() {
        authorizedAddresses[msg.sender] = true;
    }

    // event for subgraph
    event UpdatedAuthorization(address indexed target, bool authorized);

    /* ========== MODIFIERS ========== */

    modifier onlyManagers() {
        _onlyManagers();
        _;
    }

    function _onlyManagers() internal {
        require(authorizedAddresses[msg.sender] == true);
    }

    /* ========== CORE FUNCTIONS ========== */

    /**
     * @notice Checkpoints or distributes fees and then checkpoints.
     * @dev Throws if the caller is not approved as a manager. Will also revert if
     *  both actions have been called this epoch or if we are out of SCREAM to distribute.
     */
    function weeklyPayoutAndCheckpoint() external onlyManagers {
        // check if we should donate + checkpoint, checkpoint, or neither

        // lastTokenTime will be in our current epoch if we have already started the new epoch
        // thus, our next action will be distro of funds
        // then, if the last tokenTime is in the prior epoch, we know we can start the new one

        // find out the last time we checkpointed
        uint256 lastTokenTime = feeDistributor.last_token_time();
        uint256 lastTokenTimeEpoch = lastTokenTime / 1 weeks;

        // check our current epoch
        uint256 currentEpoch = block.timestamp / 1 weeks;

        // last payout epoch
        uint256 lastPayoutEpoch = lastPayoutTime / 1 weeks;

        // we can checkpoint if it's a new epoch
        if (currentEpoch > lastTokenTimeEpoch) {
            feeDistributor.checkpoint_token();
            return;
        } else if (currentEpoch > lastPayoutEpoch) {
            // calculate our weekly amount, decreases by 10 each week
            uint256 thisWeek = lastPayoutAmount - 10e18;

            // send our weekly rewards and checkpoint
            if (thisWeek > 0) {
                scream.transfer(address(feeDistributor), thisWeek);
                feeDistributor.checkpoint_token();

                // update our amounts
                lastPayoutAmount = thisWeek;
                lastPayoutTime = block.timestamp;
                return;
            }
        }
        // revert otherwise
        revert();
    }

    /**
     * @notice Controls whether a non-gov address can adjust certain params.
     * @dev Throws if the caller is not current owner.
     * @param _target The address to add/remove authorization for.
     * @param _value Boolean to grant or revoke access.
     */
    function setAuthorized(address _target, bool _value) external onlyOwner {
        authorizedAddresses[_target] = _value;
        emit UpdatedAuthorization(_target, _value);
    }

    /**
     * @notice Sweep out tokens sent here.
     * @dev Throws if the caller is not current owner.
     * @param _token Address of token to sweep.
     * @param _amount Amount of token to sweep.
     */
    function sweep(address _token, uint256 _amount) external onlyOwner {
        IERC20 token = IERC20(_token);
        token.transfer(owner(), _amount);
    }
}
